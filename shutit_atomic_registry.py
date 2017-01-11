import random
import logging
import string
import os
import inspect
from shutit_module import ShutItModule

class shutit_atomic_registry(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.cfg[self.module_id]['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		run_dir = shutit.cfg[self.module_id]['vagrant_run_dir']
		module_name = 'shutit_atomic_registry_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('command rm -rf ' + run_dir + '/' + module_name + ' && command mkdir -p ' + run_dir + '/' + module_name + ' && command cd ' + run_dir + '/' + module_name)
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		if shutit.send_and_get_output('vagrant box list | grep -w fedora25') == '':
			shutit.send('vagrant box add fedora25 ' + vagrant_image)
		vagrant_image = 'fedora25'
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(run_dir + '/' + module_name + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "atomicregistry1" do |atomicregistry1|
    atomicregistry1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    atomicregistry1.vm.hostname = "atomicregistry1.vagrant.test"
  end
end''')
		pw = shutit.get_env_pass()
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + " atomicregistry1",{'assword for':pw,'assword:':pw,'egister the system now':'n'},timeout=99999)
		except NameError:
			shutit.multisend('vagrant up atomicregistry1',{'assword for':pw,'assword:':pw,'egister the system now':'n'},timeout=99999)
		if shutit.send_and_get_output("""vagrant status | grep -w ^atomicregistry1 | awk '{print $2}'""") != 'running':
			shutit.pause_point("machine: atomicregistry1 appears not to have come up cleanly")


		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}
		machines.update({'atomicregistry1':{'fqdn':'atomicregistry1.vagrant.test'}})
		ip = shutit.send_and_get_output('''vagrant landrush ls | grep -w ^''' + machines['atomicregistry1']['fqdn'] + ''' | awk '{print $2}' ''')
		machines.get('atomicregistry1').update({'ip':ip})

		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			root_password = 'root'
			# Workaround for docker networking issues + landrush.
			shutit.send("""echo "$(host -t A index.docker.io | grep has.address | head -1 | awk '{print $NF}') index.docker.io" >> /etc/hosts""")
			shutit.send("""echo "$(host -t A registry-1.docker.io | grep has.address | head -1 | awk '{print $NF}') registry-1.docker.io" >> /etc/hosts""")
			shutit.send("""echo "$(host -t A auth.docker.io | grep has.address | head -1 | awk '{print $NF}') auth.docker.io" >> /etc/hosts""")
			shutit.send("sed -i 's/nameserver.*/nameserver 8.8.8.8/' /etc/resolv.conf")
			shutit.multisend('passwd',{'assword:':root_password})
			shutit.send("""sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config""")
			shutit.send("""sed -i 's/.*PasswordAuthentication.*/PasswordAuthentication yes/g' /etc/ssh/sshd_config""")
			shutit.send('service ssh restart || systemctl restart sshd')
			shutit.multisend('ssh-keygen',{'Enter':'','verwrite':'n'})
			shutit.logout()
			shutit.logout()
		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			for copy_to_machine in machines:
				for item in ('fqdn','ip'):
					shutit.multisend('ssh-copy-id root@' + machines[copy_to_machine][item],{'assword:':root_password,'ontinue conn':'yes'})
			shutit.logout()
			shutit.logout()
		shutit.login(command='vagrant ssh ' + sorted(machines.keys())[0])
		shutit.login(command='sudo su -',password='vagrant')
		#shutit.install('git')
		#shutit.install('docker')
		#shutit.install('atomic')
		#shutit.install('python-dateutil')
		#shutit.send('systemctl start docker')

		# Standard reg + origin - from: https://github.com/projectatomic/atomic-enterprise
		# Is this the full atomic registry?
		#
		#shutit.send('docker run -d --name "origin" --privileged --net=host -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys:ro -v /var/lib/docker:/var/lib/docker:rw -v /var/lib/openshift/openshift.local.volumes:/var/lib/openshift/openshift.local.volumes openshift/origin start')
		#shutit.login(command='docker exec -it origin bash')
		#shutit.logout('oadm registry --credentials=./openshift.local.config/master/openshift-registry.kubeconfig')



		# Did not work - no image - from: http://www.projectatomic.io/registry/
		#
		shutit.send('mkdir -p /var/lib/atomic-registry/registry')
		shutit.send('atomic install projectatomic/atomic-registry-install ' + ip)
		shutit.send('systemctl enable --now atomic-registry-master.service')
		shutit.send('/var/run/setup-atomic-registry.sh ' + ip)



		# Did not work - test failed - from: https://github.com/projectatomic/atomic-enterprise
		#
		#shutit.send('git clone https://github.com/openshift/origin')
		#shutit.send('cd origin/examples/atomic-registry')
		#shutit.send('''sed -i 's/dnf/yum/g' Makefile''')
		#shutit.send('make all-systemd')

		shutit.pause_point('Do as you will!')

		shutit.logout()
		shutit.logout()
		shutit.log('''Vagrantfile created in: ''' + shutit.cfg[self.module_id]['vagrant_run_dir'] + '/' + module_name,add_final_message=True,level=logging.DEBUG)
		shutit.log('''Run:

	cd ''' + shutit.cfg[self.module_id]['vagrant_run_dir'] + '/' + module_name + ''' && vagrant status && vagrant landrush ls

To get a picture of what has been set up.''',add_final_message=True,level=logging.DEBUG)
		return True


	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='https://getfedora.org/atomic/download/download-cloud-splash?file=https://download.fedoraproject.org/pub/alt/atomic/stable/Fedora-Atomic-25-20170106.0/CloudImages/x86_64/images/Fedora-Atomic-Vagrant-25-20170106.0.x86_64.vagrant-virtualbox.box')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='true')
		shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'vagrant_run_dir',default='/tmp')
		return True

	def test(self, shutit):
		return True

	def finalize(self, shutit):
		return True

	def is_installed(self, shutit):
		# Destroy pre-existing, leftover vagrant images.
		shutit.run_script('''#!/bin/bash
MODULE_NAME=ESS
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
set -x
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $NF}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep ${MODULE_NAME} | awk '{print $NF}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs -n1 virsh destroy
fi
''')
		return False

	def start(self, shutit):
		return True

	def stop(self, shutit):
		return True

def module():
	return shutit_atomic_registry(
		'git.shutit_atomic_registry.shutit_atomic_registry', 1280442025.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
