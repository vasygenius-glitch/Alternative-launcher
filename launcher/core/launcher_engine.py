import subprocess
import os
import minecraft_launcher_lib
from launcher.utils.logger import get_logger
from launcher.utils.config import ConfigManager

log = get_logger("LauncherEngine")

class LauncherEngine:
    def __init__(self, instance_manager):
        self.im = instance_manager
        self.config = ConfigManager()

    def _aikar_flags(self):
        return [
            "-XX:+UseG1GC",
            "-XX:+ParallelRefProcEnabled",
            "-XX:MaxGCPauseMillis=200",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+DisableExplicitGC",
            "-XX:+AlwaysPreTouch",
            "-XX:G1NewSizePercent=30",
            "-XX:G1MaxNewSizePercent=40",
            "-XX:G1HeapRegionSize=8M",
            "-XX:G1ReservePercent=20",
            "-XX:G1HeapWastePercent=5",
            "-XX:G1MixedGCCountTarget=4",
            "-XX:InitiatingHeapOccupancyPercent=15",
            "-XX:G1MixedGCLiveThresholdPercent=90",
            "-XX:G1RSetUpdatingPauseTimePercent=5",
            "-XX:SurvivorRatio=32",
            "-XX:+PerfDisableSharedMem",
            "-XX:MaxTenuringThreshold=1",
            "-Dusing.aikars.flags=https://mcflags.emc.gs",
            "-Daikars.new.flags=true"
        ]

    def install_and_get_version(self, instance_id, progress_callback=None):
        instance = self.im.get_instance(instance_id)
        if not instance:
            raise ValueError("Instance not found")

        mc_dir = self.im.get_instance_dir(instance_id)
        mc_version = instance['mc_version']
        loader = instance['loader']
        loader_version = instance['loader_version']

        # Vanilla Callback Wrapper
        def vanilla_cb(progress, max_progress, desc=""):
            if progress_callback:
                # scale vanilla to 0-30%
                p = (progress / max_progress) * 30 if max_progress > 0 else 0
                progress_callback(p, f"Vanilla: {desc}")

        cb_dict_vanilla = {
            "setStatus": lambda text: vanilla_cb(0, 100, text),
            "setProgress": lambda p: vanilla_cb(p, 100, ""),
            "setMax": lambda m: None
        }

        # Smart Discovery optimization
        default_mc = self.im.default_mc
        if os.path.exists(default_mc):
            # Tell MLL to use the default dir as the main source to avoid redownloading common assets
            options_install = {"resolution": {}}
            log.info("Using existing .minecraft for asset resolution.")
            # Note: MLL natively handles caching if the directory already has files
            # But we can also symlink 'assets' to save disk space if we want.
            try:
                asset_link = os.path.join(mc_dir, "assets")
                default_assets = os.path.join(default_mc, "assets")
                if not os.path.exists(asset_link) and os.path.exists(default_assets):
                    # Try symlink, fallback to copy/ignore
                    if os.name != 'nt':
                        os.symlink(default_assets, asset_link)
            except Exception as e:
                log.debug(f"Could not symlink assets: {e}")

        # Pre-flight Java check for modern versions
        if mc_version.startswith("1.17") or mc_version.startswith("1.18") or mc_version.startswith("1.19") or mc_version.startswith("1.20") or mc_version.startswith("1.21"):
            from launcher.core.system_info import SystemInfo
            java_path = self.config.get("java", "java_path", "")
            if java_path:
                v = SystemInfo._verify_java_executable(java_path)
                if v and "1.8" in v:
                    raise Exception("Для этой версии Minecraft требуется Java 17 или новее. У вас указана Java 8. Измените настройки.")

        # 1. Install Vanilla
        log.info(f"Installing Vanilla {mc_version} to {mc_dir}")
        minecraft_launcher_lib.install.install_minecraft_version(mc_version, mc_dir, callback=cb_dict_vanilla)

        # 2. Install Loader
        target_version_id = mc_version

        if loader == "forge":
            if not loader_version or loader_version == "latest":
                loader_version = minecraft_launcher_lib.forge.find_forge_version(mc_version)

            def forge_cb(progress, max_progress, desc=""):
                if progress_callback:
                    # scale forge to 30-100%
                    p = 30 + ((progress / max_progress) * 70 if max_progress > 0 else 0)
                    progress_callback(p, f"Forge: {desc}")

            cb_dict_forge = {
                "setStatus": lambda text: forge_cb(0, 100, text),
                "setProgress": lambda p: forge_cb(p, 100, ""),
                "setMax": lambda m: None
            }

            # Usually MLL forge installer creates an ID matching the exact forge string or appends -forge-
            # We must strictly check if the json was generated.
            log.info(f"Installing Forge {loader_version}")
            minecraft_launcher_lib.forge.install_forge_version(loader_version, mc_dir, callback=cb_dict_forge)

            target_version_id = loader_version

            # Strict Validation of JSON
            expected_json = os.path.join(mc_dir, "versions", target_version_id, f"{target_version_id}.json")
            if not os.path.exists(expected_json):
                # Sometimes MLL formats Forge IDs differently (e.g. 1.20.1-forge-47.4.5)
                alt_id = f"{mc_version}-forge-{loader_version.split('-')[-1]}"
                alt_json = os.path.join(mc_dir, "versions", alt_id, f"{alt_id}.json")

                if os.path.exists(alt_json):
                    target_version_id = alt_id
                else:
                    raise Exception(f"Forge installation failed. The expected version manifest ({target_version_id}.json) was not found in {mc_dir}/versions/. Antivirus might be blocking it.")

        elif loader == "fabric":
             log.info("Installing Fabric")
             minecraft_launcher_lib.fabric.install_fabric(mc_version, mc_dir)
             target_version_id = f"fabric-loader-{loader_version}-{mc_version}"

             expected_json = os.path.join(mc_dir, "versions", target_version_id, f"{target_version_id}.json")
             if not os.path.exists(expected_json):
                 raise Exception(f"Fabric installation failed. Manifest ({target_version_id}.json) not found.")

        return target_version_id

    def build_command_and_launch(self, instance_id, account, version_id):
        mc_dir = self.im.get_instance_dir(instance_id)

        # Load Java settings
        from launcher.core.system_info import SystemInfo
        java_path = self.config.get("java", "java_path", "")
        custom_args_str = self.config.get("java", "custom_args", "")
        gc_type = self.config.get("java", "gc_type", "G1GC")
        ram_min = self.config.get("java", "ram_min", None)
        ram_max = self.config.get("java", "ram_max", None)

        # Use optimal dynamic flags calculated by SystemInfo, which inherently considers the RAM
        jvm_args = SystemInfo.get_jvm_args(gc_type=gc_type, custom_ram_min=ram_min, custom_ram_max=ram_max)

        # Override RAM if user explicitly set custom flags, though otherwise SystemInfo handled it
        if custom_args_str:
            jvm_args.extend(custom_args_str.split())

        options = {
            "username": account["username"],
            "uuid": account["uuid"],
            "token": account["access_token"],
            "jvmArguments": jvm_args
        }

        if java_path and os.path.exists(java_path):
            options["executablePath"] = java_path

        log.info("Generating launch command...")
        command = minecraft_launcher_lib.command.get_minecraft_command(version_id, mc_dir, options)

        log.info("Launching JVM...")
        # Return the Popen object so the app can monitor it
        return subprocess.Popen(command, cwd=mc_dir)
