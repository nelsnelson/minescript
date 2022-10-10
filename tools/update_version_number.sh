#!/bin/bash

# SPDX-FileCopyrightText: © 2022 Greg Christiana <maxuser@minescript.net>
# SPDX-License-Identifier: MIT

# Updates the Minescript version number across configs and sources. If
# --branch_docs is specified, docs/README.md is branched to
# docs/v<old_version>/README.md; if --nobranch_docs is specified, docs are not
# branched. Pass -n for a dry run, i.e. print the commands that would run or
# the old version strings that would be matched, but do not rewrite the version
# number.
#
# This script must be run from the 'minescript' directory, and expects 'fabric'
# and 'forge' subdirectories.
#
# Usage:
#   tools/update_version_number.sh <old_version> <new_versio> --branch_docs|--nobranch_docs -n
#
# Example:
#   Update version number from 2.1 to 2.2 and branch docs from to docs/v2.1:
#   $ tools/update_version_number.sh 2.1 2.2 --branch_docs

old_version=${1:?"Error: old version number required."}
new_version=${2:?"Error: new version number required."}
branch_docs_arg=${3:?"Error: must specify --branch_docs or --nobranch_docs"}

# Discard the fixed-position args.
shift 3

if [[ $branch_docs_arg = "--branch_docs" ]]; then
  branch_docs=1
elif [[ $branch_docs_arg = "--nobranch_docs" ]]; then
  branch_docs=0
else
  echo "Required 3rd arg must be --branch_docs or --nobranch_docs." >&2
  exit 1
fi

dry_run=0

while (( "$#" )); do
  case $1 in
    -n)
      dry_run=1
      ;;
    *)
      echo "Unrecognized arg: $1"  >&2
      exit 2
      ;;
  esac
  shift
done

old_version_re=$(echo $old_version |sed 's/\./\\./g')

if [ "$(basename $(pwd))" != "minescript" ]; then
  echo "update_version_number.sh must be run from 'minescript' directory." >&2
  exit 3
fi

function check_subdir_exists {
  subdir="$1"
  if [ ! -d "$subdir" ]; then
    echo "update_version_number.sh cannot find '${subdir}' subdirectory." >&2
    exit 4
  fi
}

check_subdir_exists fabric
check_subdir_exists forge
check_subdir_exists docs

if [ ! -e docs/README.md ]; then
  echo "Required file missing: docs/README.md" >&2
  exit 5
fi

if [ $branch_docs = 1 ]; then
  old_version_docs=docs/v${old_version}
  if [ $dry_run = 0 ]; then
    mkdir "$old_version_docs" || (echo "$old_version_docs already exists." >&2; exit 6)

    old_version_readme=$old_version_docs/README.md
    cp -p docs/README.md "$old_version_readme"

    # Insert a blank line and "Latest version: ..." after "Previous version: ...".
    sed -i '' -e '/^Previous version:/a \
Latest version: [latest](../README.md)' "$old_version_readme"
    sed -i '' -e '/^Previous version:/a \
' "$old_version_readme"

  else
    echo mkdir "$old_version_docs" || (echo "$old_version_docs already exists." >&2; exit 7)
  fi
fi

# Rewrite version in first line of docs/README.md and linked "Previous version".
if [ $dry_run = 0 ]; then
  sed -i '' -e \
      "s/^## Minescript v${old_version} docs$/## Minescript v${new_version} docs/" \
      docs/README.md

  sed -i '' -e \
      "s#^Previous version: \[v.*\](v.*/README.md)#Previous version: [v${old_version}](v${old_version}/README.md)#" docs/README.md
else
  grep "^## Minescript v${old_version} docs$" docs/README.md
  grep '^Previous version: \[v.*\](v.*/README.md)' docs/README.md
fi

for x in {fabric,forge}/gradle.properties; do
    if [ $dry_run = 0 ]; then
      sed -i '' -e "s/mod_version=${old_version_re}$/mod_version=${new_version}/" $x
    else
      grep -H "$old_version_re" $x
    fi
done

for x in $(tools/find_version_number.sh $old_version -l |grep '\.py$'); do
    if [ $dry_run = 0 ]; then
      sed -i '' -e "s/v${old_version_re} /v${new_version} /" $x
    else
      grep -H "v${old_version_re} " $x
    fi
done
