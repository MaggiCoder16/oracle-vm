import subprocess
import json
import time
from datetime import datetime
import sys

# --- FINAL VERIFIED CONFIGURATION ---
IMAGE_ID = "ocid1.image.oc1.ap-mumbai-1.aaaaaaaagj6eib2rslvji6xgh2e32naoyyfyedm2iy5mcpm2hfqphtixmbpq"
COMPARTMENT_ID = "ocid1.tenancy.oc1..aaaaaaaawcbqn5ajlg573v5aetw6j7hxpxyvzpp3cj7e3d3pnv2xocdzmvbq"
SUBNET_ID = "ocid1.subnet.oc1.ap-mumbai-1.aaaaaaaauukelgwzticy2xr5az7xnr57rtfo223usf7wr5kpubqmjwbugmwq"
AD_NAME = "igqw:AP-MUMBAI-1-AD-1"
SSH_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDPxk2e4zDA7Maw92PCykPpeEkVLTVjA25uohXgtLn691n2c+RjD9VNDSZ343ZaDYfZzf4sK3BT+VEQH0Iui0+iBAlGntcarkWZx0TEcHakNi4Hm2cHDC2OxK/z8Xb9DpZ1QII8604CQYRXzyP52a3ueT+r+26K/Um/O0WaRKlCLKdcfJ2r1x7FgpGz0z8EvNdAEQap0jgFh3KD0Ip2dYdcLLKo7Bff0l2N4vVOoqJNTn0vrVPC0PnavuMSkKBtUgpkgvAhmu07WBMI8vzurV5f+3AzSeegNP/ZLuWVn6vEAzihgR3ht6uJJ8YcphNv+ufMUjVB04C1Orme5TI0yCjv thisa@Aarav"

FAULT_DOMAINS = ["FAULT-DOMAIN-1", "FAULT-DOMAIN-2", "FAULT-DOMAIN-3"]
LOG_FILE = "vm_snag.log"

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def launch_instance(attempt_num, fault_domain):
    log(f"Attempt #{attempt_num} to snag VM in {fault_domain}...")

    shape_config = json.dumps({"ocpus": 4, "memoryInGBs": 24})
    metadata = json.dumps({"ssh_authorized_keys": SSH_KEY})

    command = [
        "oci", "compute", "instance", "launch",
        "--compartment-id", COMPARTMENT_ID,
        "--availability-domain", AD_NAME,
        "--fault-domain", fault_domain,
        "--subnet-id", SUBNET_ID,
        "--image-id", IMAGE_ID,
        "--shape", "VM.Standard.A1.Flex",
        "--display-name", "codunotBOT",
        "--assign-public-ip", "true",
        "--shape-config", shape_config,
        "--metadata", metadata
    ]

    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=300)
        if process.returncode == 0:
            log("[SUCCESS] VM created successfully!")
            return True
        else:
            err = process.stderr
            if "Out of host capacity" in err or "500" in err or "LimitExceeded" in err:
                log("[CAPACITY] VM not available in this fault domain. Retrying...")
            elif "TooManyRequests" in err or "429" in err:
                log("[THROTTLE] Too many requests! Waiting longer before retry...")
                time.sleep(120)
            else:
                log(f"[ERROR]\n{err}")
            return False
    except Exception as e:
        log(f"System Error: {e}")
        return False

attempt = 1
fd_index = 0

while True:
    current_fd = FAULT_DOMAINS[fd_index]
    if launch_instance(attempt, current_fd):
        break
    attempt += 1
    fd_index = (fd_index + 1) % len(FAULT_DOMAINS)
    time.sleep(60)
