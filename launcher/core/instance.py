import os
import json
import uuid
import shutil
import minecraft_launcher_lib
from launcher.utils.logger import get_logger

log = get_logger("InstanceMgr")

class InstanceManager:
    """
    Manages Minecraft instances (folders, versions, loaders).
    """
    def __init__(self, instances_dir="launcher_data/instances"):
        self.instances_dir = os.path.abspath(instances_dir)
        os.makedirs(self.instances_dir, exist_ok=True)

    def _get_instance_json_path(self, instance_id):
        return os.path.join(self.instances_dir, instance_id, "instance.json")

    def create_instance(self, name, mc_version, loader="forge", loader_version="latest"):
        instance_id = str(uuid.uuid4())
        inst_dir = os.path.join(self.instances_dir, instance_id)
        os.makedirs(inst_dir, exist_ok=True)

        # Determine specific loader version if "latest"
        actual_loader_version = loader_version
        if loader_version == "latest" and loader == "forge":
             # We can fetch latest forge version using mll
             actual_loader_version = minecraft_launcher_lib.forge.find_forge_version(mc_version)
             # Fallback if mll fails to find it (rare but happens)
             if not actual_loader_version:
                 log.warning("Could not auto-detect latest forge version, using vanilla for now.")
                 loader = "vanilla"

        data = {
            "id": instance_id,
            "name": name,
            "mc_version": mc_version,
            "loader": loader,
            "loader_version": actual_loader_version,
            "created_at": __import__("time").time()
        }

        with open(self._get_instance_json_path(instance_id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        log.info(f"Created instance: {name} ({mc_version} - {loader})")
        return instance_id

    def get_instances(self):
        instances = []
        for d in os.listdir(self.instances_dir):
            json_path = self._get_instance_json_path(d)
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        instances.append(json.load(f))
                except Exception as e:
                    log.error(f"Failed to read instance {d}: {e}")
        return instances

    def get_instance(self, instance_id):
        if not instance_id:
            return None

        json_path = self._get_instance_json_path(instance_id)
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def delete_instance(self, instance_id):
        inst_dir = os.path.join(self.instances_dir, instance_id)
        if os.path.exists(inst_dir):
            try:
                shutil.rmtree(inst_dir)
                log.info(f"Deleted instance: {instance_id}")
                return True
            except Exception as e:
                log.error(f"Failed to delete instance {instance_id}: {e}")
        return False

    def get_instance_dir(self, instance_id):
        return os.path.join(self.instances_dir, instance_id)
