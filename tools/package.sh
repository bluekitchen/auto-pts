#!/usr/bin/env sh

# get absolute path
TOOL_DIR=`dirname "$0"`
REPO_ROOT=`realpath ${TOOL_DIR}/..`

# get tag from git
tag=`git tag --points-at`

# get git version
commit=`git rev-parse --short HEAD`

# use tag if available
if [ -z "$tag" ]
then
    version=${commit}
else
    version=${tag}-${commit}
fi

# zip repository
archive_zip="auto-pts-${version}.zip"
echo Create ${archive_zip}
cd ${REPO_ROOT} && git archive --format=zip -o ${archive_zip} HEAD .

echo Done
