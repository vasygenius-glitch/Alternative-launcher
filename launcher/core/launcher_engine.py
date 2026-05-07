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

        # 1. Install Vanilla
        log.info(f"Installing Vanilla {mc_version} to {mc_dir}")
        minecraft_launcher_lib.install.install_minecraft_version(mc_version, mc_dir, callback=cb_dict_vanilla)

        # 2. Install Loader
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

            log.info(f"Installing Forge {loader_version}")
            minecraft_launcher_lib.forge.install_forge_version(loader_version, mc_dir, callback=cb_dict_forge)
            return loader_version # Forge versions act as the ID in MLL

        elif loader == "fabric":
             # Similar approach for fabric (requires fabric installer lib which MLL supports)
             log.info("Installing Fabric")
             minecraft_launcher_lib.fabric.install_fabric(mc_version, mc_dir)
             # Fabric version ID usually follows a pattern
             return f"fabric-loader-{loader_version}-{mc_version}"

        return mc_version # Vanilla fallback

    def build_command_and_launch(self, instance_id, account, version_id):
        mc_dir = self.im.get_instance_dir(instance_id)

        # Load RAM settings
        ram_min = self.config.get("java", "ram_min", 2048)
        ram_max = self.config.get("java", "ram_max", 4096)
        java_path = self.config.get("java", "java_path", "")
        custom_args_str = self.config.get("java", "custom_args", "")

        jvm_args = self._aikar_flags()
        jvm_args.extend([f"-Xms{ram_min}M", f"-Xmx{ram_max}M"])
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
        subprocess.Popen(command, cwd=mc_dir)
