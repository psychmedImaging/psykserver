#! /bin/bash
if [ $# -eq 0 ]; then
	version="latest"
else
	version=$1
fi
id_num=$(id -u) 
port_num=${id_num: -4}
username=$(whoami)
group_name=employee
group_id=`getent group $group_name | cut -d: -f3`
ip_address=`hostname -I | cut -d' ' -f1`
storage_mount="/storage/$username"
argos_mount="$storage_mount/argos"
wharf_mount="$storage_mount/wharf"

if [ ! -d $argos_mount ]; then
	mkdir -p $argos_mount
fi

container_name="neurodesktop_${version}_${username}"
workspace="myworkspace"
timeout=120

if [ ! "$(sudo docker ps -a -q -f name=$container_name)" ]; then
      if `mountpoint -q $argos_mount`; then
	 echo "Argos is already mounted"
      else
         echo "Mounting Argos to $argos_mount"
         echo "Please enter your password for Argos:"
         sudo mount -t cifs //argos.storage.uu.se/MyGroups$/ $argos_mount \
            -o domain=user,user=$username,uid=$username,gid=$group_name,dir_mode=0700,file_mode=0600
      fi 
      if `mountpoint -q $wharf_mount`; then
	 echo "UPPMAX Wharf is already mounted"
      else
         echo "Mounting UPPMAX Wharf to $wharf_mount"
	 echo "Please enter your UPPMAX user name (leave empty to skip):"
	 read wharf_id
	 if [ $wharf_id ]; then
            echo "Enter your UPPMAX project name:"
            read proj_id
            if [ ! -d $wharf_mount ]; then
        	mkdir -p $wharf_mount
            fi
            echo "Please enter your password for UPPMAX:"
            sshfs $wharf_id@bianca-sftp.uppmax.uu.se:$proj_id/$wharf_id $wharf_mount \
   	       -o ServerAliveInterval=60
	 fi
      fi 
      sudo docker run \
      --shm-size=1gb --detach --privileged --user=root --name $container_name \
      -v ~/neurodesktop-storage:/neurodesktop-storage \
      -v $storage_mount:/data \
      -e MATLABPATH="/data/argos/Iron/common_software" \
      -e JUPYTERLAB_WORKSPACES_DIR="/home/jovyan/data" \
      -e NB_UID="$id_num" -e NB_GID=$group_id \
      -p $port_num:8888 \
      -e NEURODESKTOP_VERSION=$version vnmd/neurodesktop:$version

#      --mac-address 02:42:ac:11:00:02 \

      echo "Waiting for neurodesktop to start"
      for ((i=1; i<=timeout; i++)); do 
         if [ $i -eq $timeout ]; then
            echo >&2 giving up
	    echo >&2 type sudo docker logs $container_name to debug 
	    exit 1
	 fi
         if sudo docker logs $container_name 2>&1 | awk '{if ($0 ~ /To access/) {exit 0}} ENDFILE{exit -1}'; then
	    break
	 fi
	 echo -n "."
	 sleep 1
      done
      sudo docker exec $container_name jupyter lab workspaces export $workspace
   else
      echo "The docker container is already running"
fi

token=$(sudo docker exec $container_name jupyter server list 2>/dev/null | grep http -s | sed 's/.*=\(.*\)\ ::.*/\1/')

echo ""
echo "To clean up:"
echo "sudo docker rm -f ${container_name}"
echo ""
echo "To run neurodesktop, copy the following to your browser:"
echo "http://${ip_address}:$port_num/lab/workspaces/$workspace?token=$token"
exit 0
