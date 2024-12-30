#!/usr/bin/env bash

if [ -z "$@" ]; then
    EL_RELEASES='7 9'
else
    EL_RELEASES="$@"
fi

RELEASE=$(grep '^%define libmoose_release' ./rpmbuild/SPECS/python3-libmoose.spec | awk '{print $NF}')
VERSION=$(grep '^%define libmoose_version' ./rpmbuild/SPECS/python3-libmoose.spec | awk '{print $NF}')

echo "$(date) - creating tarball for python3-libmoose-${VERSION}"
mkdir -p ./dist ./python3-libmoose-${VERSION}/libmoose
cp -a ./setup.py ./python3-libmoose-${VERSION}/
cp -a ./src/*py ./python3-libmoose-${VERSION}/libmoose/
python3 -m build --outdir ./dist ./python3-libmoose-${VERSION}

echo "$(date) - cleaning up"
mv -v ./dist/libmoose-0.1.tar.gz ./rpmbuild/SOURCES/
rm -rv ./dist ./python3-libmoose-${VERSION}/


for el_release in $EL_RELEASES; do
    mock_config=libmoose-el-${el_release}-x86_64
    mock_dir=/var/lib/mock/${mock_config}/result

    echo "$(date) - building el${el_release} SRPM"
    sudo mock -v -r ./rpmbuild/mock/${mock_config}.cfg --buildsrpm --spec ./rpmbuild/SPECS/python3-libmoose.spec --source ./rpmbuild/SOURCES/ &> ./rpmbuild/${mock_config}.srpm.log
    if [ -f "${mock_dir}/python3-libmoose-${VERSION}-${RELEASE}.el${el_release}.src.rpm" ]; then
        echo "$(date) - copying el${el_release} SRPM"
        cp -v ${mock_dir}/python3-libmoose-${VERSION}-${RELEASE}.el${el_release}.src.rpm ./rpmbuild/SRPMS/
    else
        echo "$(date) - error building SRPM. Check logs in ${mock_dir}/ or ./rpmbuild/${mock_config}.srpm.log"
        exit 1
    fi

    echo "$(date) - building el${el_release} RPM"
    sudo mock -v -r ./rpmbuild/mock/${mock_config}.cfg ./rpmbuild/SRPMS/python3-libmoose-${VERSION}-${RELEASE}.el${el_release}.src.rpm &> ./rpmbuild/${mock_config}.rpm.log
    if [ -f "${mock_dir}/python3-libmoose-${VERSION}-${RELEASE}.el${el_release}.noarch.rpm" ]; then
        echo "$(date) - copying el${el_release} RPM"
        cp -v ${mock_dir}/python3-libmoose-${VERSION}-${RELEASE}.el${el_release}.noarch.rpm ./rpmbuild/RPMS/
    else
        echo "$(date) - error building RPM. Check logs in ${mock_dir}/ or ./rpmbuild/${mock_config}.rpm.log"
        exit 1
    fi
done

