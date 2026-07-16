#!/usr/bin/env zsh
set -e
cd $(git rev-parse --show-toplevel)
copier update -a ./copier-instances/.copier-answers-dl_template_copier-292e6c68-40bf-77ab-34cb-a63ef586b606.yml --trust
