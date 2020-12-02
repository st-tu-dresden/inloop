from collections import OrderedDict

config = OrderedDict()
config["GITLOAD_URL"] = ("", "URL of the Git task repository.")
config["GITLOAD_BRANCH"] = ("main", "Git branch to be used for the checkout.")

fieldsets = {"Gitload settings": ["GITLOAD_URL", "GITLOAD_BRANCH"]}
