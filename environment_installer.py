import os
from utils import *
import dotenv

CODESPACE_NAME = os.environ.get("CODESPACE_NAME", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
REPOSITORY_NAME = os.environ.get("RepositoryName", "")

# Install RunMe
RUNME_CLI_VERSION = "3.13.2"
EASYTRADE_CHART_VERSION = "1.5.0"
run_command(["mkdir", "runme_binary"])
run_command(["wget", "-O", "runme_binary/runme_linux_x86_64.tar.gz", f"https://download.stateful.com/runme/{RUNME_CLI_VERSION}/runme_linux_x86_64.tar.gz"])
run_command(["tar", "-xvf", "runme_binary/runme_linux_x86_64.tar.gz", "--directory", "runme_binary"])
run_command(["sudo", "mv", "runme_binary/runme", "/usr/local/bin"])
run_command(["rm", "-rf", "runme_binary"])

# Build DT environment URLs
DT_TENANT_APPS, DT_TENANT_LIVE = build_dt_urls(dt_env_id=DT_ENVIRONMENT_ID, dt_env_type=DT_ENVIRONMENT_TYPE)

# Write .env file
# Required because user interaction needs DT_TENANT_LIVE during the tutorial
# This ONLY creates the .env file. YOU are responsible for `source`ing it!!
# So we tell user to source .env
dotenv.set_key(dotenv_path=".env", key_to_set="DT_APPS_URL", value_to_set=DT_TENANT_APPS, export=True)
dotenv.set_key(dotenv_path=".env", key_to_set="DT_URL", value_to_set=DT_TENANT_LIVE, export=True)

subprocess.run(["kind", "create", "cluster", "--config", ".devcontainer/kind-cluster.yml", "--wait", STANDARD_TIMEOUT])

print("Installing Dynatrace OneAgent...")
install_dynatrace_oneagent(dt_tenant_live=DT_TENANT_LIVE)

print("Installing Easytrade...")
subprocess.run([
    "helm", "upgrade", "--install", "easytrade",
    "oci://europe-docker.pkg.dev/dynatrace-demoability/helm/easytrade",
    "--version", EASYTRADE_CHART_VERSION,
    "--namespace", "easytrade",
    "--create-namespace",
    "--atomic",
    "--set", "aggregator-service.enabled=false",
    "--set", "calculationservice.enabled=false",
    "--set", "contentcreator.enabled=false",
    "--set", "rabbitmq.enabled=false",
    "--set", "accountservice.resources.requests.cpu=10m",
    "--set", "broker-service.resources.requests.cpu=10m",
    "--set", "credit-card-order-service.resources.requests.cpu=50m",
    "--set", "db.resources.requests.cpu=50m",
    "--set", "engine.resources.requests.cpu=10m",
    "--set", "feature-flag-service.resources.requests.cpu=10m",
    "--set", "frontend.resources.requests.cpu=10m",
    "--set", "frontendreverseproxy.resources.requests.cpu=10m",
    "--set", "loadgen.resources.requests.cpu=50m",
    "--set", "loginservice.resources.requests.cpu=10m",
    "--set", "manager.resources.requests.cpu=10m",
    "--set", "offerservice.resources.requests.cpu=10m",
    "--set", "pricing-service.resources.requests.cpu=10m",
    "--set", "problem-operator.resources.requests.cpu=10m",
    "--set", "third-party-service.resources.requests.cpu=10m",
])

# Restart backend once for the Live Debugger, if OneAgent isn't started yet it may not pick it up
time.sleep(10)
run_command(["kubectl", "rollout", "restart", "deployment/easytrade-credit-card-order-service", "-n", "easytrade"])

if CODESPACE_NAME.startswith("dttest-"):
    run_command(["pip", "install", "-r", f"/workspaces/{REPOSITORY_NAME}/.devcontainer/testing/requirements.txt", "--break-system-packages"])
    run_command(["python",  f"/workspaces/{REPOSITORY_NAME}/.devcontainer/testing/testharness.py"])

    # Testing finished. Destroy the codespace
    run_command(["gh", "codespace", "delete", "--codespace", CODESPACE_NAME, "--force"])
else:
    send_startup_ping(demo_name="TODO_SET_THIS_VALUE")
