import paramiko
import time
import thread

class VideoPi(paramiko.SSHClient):
    def __init__(self):
        paramiko.SSHClient.__init__(self)
        self.ip = '192.168.1.193'
        self.port = 22
        # self.load_host_keys()
        self._username = 'pi'
        self._password = '2020'
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect(self.ip, port=self.port, username=self._username,
                     key_filename='../media/keys/pi-camera')

    def _execute_command(self, command, background=True):
        if background:
            thread.start_new_thread(self.exec_command, (command,))
        else:
            self.exec_command(command)
        # print(output[1].readlines())
        # if len(output[2].readlines()):
        #     print("[Error] SSH '" + command + "' returned an error")
        # return output

    def start_recording(self, filename, time=False):
        output_file = filename + '.h264'
        raspivid = '/usr/bin/raspivid -o ' + output_file
        if not time:
            command = raspivid + ' -t 0'
        else:
            command = raspivid + ' -t ' + str(time)
        self._execute_command(command)
        return

    def stop_recording(self):
        command = '/usr/bin/pkill raspivid'
        self._execute_command(command, False)
        self.close_connection()
        return True

    def close_connection(self):
        self.close()
        return True


if __name__ == '__main__':
    client = VideoPi()
    client.start_recording("tet")
    print("sleeping")
    time.sleep(10)
    client.stop_recording()


