import os
import platform
import psutil
import subprocess
from launcher.utils.logger import get_logger

log = get_logger("SystemInfo")

class SystemInfo:
    @staticmethod
    def get_total_ram_mb():
        try:
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except Exception as e:
            log.error(f"Failed to get total RAM: {e}")
            return 4096 # Safe fallback

    @staticmethod
    def check_disk_space(path, required_mb=1024):
        """
        Checks if there is enough free space on the disk where 'path' resides.
        Returns True if enough space, False otherwise.
        """
        try:
            # Ensure the directory exists or check its parent
            check_path = path
            while not os.path.exists(check_path):
                check_path = os.path.dirname(check_path)
                if not check_path or check_path == os.path.dirname(check_path):
                    break # Reached root

            if os.path.exists(check_path):
                usage = psutil.disk_usage(check_path)
                free_mb = usage.free / (1024 * 1024)
                if free_mb < required_mb:
                    log.error(f"Not enough disk space! Required: {required_mb}MB, Free: {free_mb:.2f}MB on {check_path}")
                    return False
                log.info(f"Disk space check passed. Free: {free_mb:.2f}MB on {check_path}")
                return True
            else:
                log.warning(f"Could not determine disk usage for path: {path}")
                return True # Optimistic fallback
        except Exception as e:
            log.error(f"Disk space check failed: {e}")
            return True # Don't block launch if check fails

    @staticmethod
    def _find_java_in_registry():
        """Scans Windows Registry for Java installations."""
        if platform.system() != "Windows":
            return []

        javas = []
        try:
            import winreg
            # Look in standard locations
            paths = [
                r"SOFTWARE\JavaSoft\Java Runtime Environment",
                r"SOFTWARE\JavaSoft\Java Development Kit",
                r"SOFTWARE\JavaSoft\JRE"
            ]
            for reg_path in paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        # Get current version
                        try:
                            curr_ver, _ = winreg.QueryValueEx(key, "CurrentVersion")
                            with winreg.OpenKey(key, curr_ver) as subkey:
                                java_home, _ = winreg.QueryValueEx(subkey, "JavaHome")
                                java_exe = os.path.join(java_home, "bin", "java.exe")
                                if os.path.exists(java_exe):
                                    javas.append(java_exe)
                        except OSError:
                            pass
                except OSError:
                    pass
        except Exception as e:
            log.debug(f"Registry scan for Java failed: {e}")
        return javas

    @staticmethod
    def _verify_java_executable(java_path):
        """Runs java -version to verify it works and get version info."""
        if not os.path.exists(java_path):
            return None
        try:
            # We use stderr because java -version outputs to stderr
            result = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # Basic parsing, e.g., java version "1.8.0_291" or openjdk version "17.0.1"
                output = result.stderr.lower()
                if "version" in output:
                     log.debug(f"Verified Java at {java_path}: {output.splitlines()[0]}")
                     return java_path
        except Exception as e:
            log.debug(f"Verification failed for {java_path}: {e}")
        return None

    @staticmethod
    def discover_java_paths():
        """Finds valid Java executables on the system."""
        valid_javas = set()

        # 1. Check Registry (Windows)
        reg_javas = SystemInfo._find_java_in_registry()
        for j in reg_javas:
            v = SystemInfo._verify_java_executable(j)
            if v: valid_javas.add(v)

        # 2. Check Environment Variables
        env_home = os.environ.get("JAVA_HOME")
        if env_home:
            exe = "java.exe" if platform.system() == "Windows" else "java"
            j = os.path.join(env_home, "bin", exe)
            v = SystemInfo._verify_java_executable(j)
            if v: valid_javas.add(v)

        # 3. Check system path (which java / where java)
        try:
            cmd = "where java" if platform.system() == "Windows" else "which java"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    j = line.strip()
                    v = SystemInfo._verify_java_executable(j)
                    if v: valid_javas.add(v)
        except Exception:
            pass

        log.info(f"Discovered {len(valid_javas)} valid Java installations.")
        return list(valid_javas)

    @staticmethod
    def auto_configure(config_manager):
        total_ram = SystemInfo.get_total_ram_mb()

        if total_ram < 8192:
            ram_min = 1024
            ram_max = min(total_ram - 2048, 4096)
            if ram_max < 1024: ram_max = 1024
        elif total_ram <= 16384:
            ram_min = 2048
            ram_max = 6144
        else:
            ram_min = 4096
            ram_max = 8192

        config_manager.set("java", "ram_min", ram_min)
        config_manager.set("java", "ram_max", ram_max)

        javas = SystemInfo.discover_java_paths()
        if javas:
            config_manager.set("java", "java_path", javas[0])

        log.info(f"Auto-configured RAM: {ram_min}-{ram_max}MB and Java: {javas[0] if javas else 'auto'}")

    @staticmethod
    def get_jvm_args():
        """
        Generates optimal JVM flags based on total RAM.
        Warns if RAM is critically low (< 8GB).
        """
        total_ram = SystemInfo.get_total_ram_mb()

        if total_ram < 8192:
            log.warning(f"Low system RAM detected ({total_ram}MB). Performance may be degraded. Recommend 8GB+ for modded Minecraft.")
            ram_min = 1024
            ram_max = min(total_ram - 2048, 4096) # Reserve at least 2GB for OS, max out at 4GB
            if ram_max < 1024: ram_max = 1024
        elif total_ram <= 16384:
            ram_min = 2048
            ram_max = 6144 # 6GB is a good sweet spot for modern packs
        else:
            ram_min = 4096
            ram_max = 8192 # Don't go too crazy, GC pauses get bad above 8GB unless specifically tuned

        # Aikar's flags optimized for G1GC (industrial standard for MC)
        flags = [
            f"-Xms{ram_min}M",
            f"-Xmx{ram_max}M",
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
            "-XX:MaxTenuringThreshold=1"
        ]

        log.info(f"Generated optimal JVM args (RAM: {ram_max}MB allocated).")
        return flags
