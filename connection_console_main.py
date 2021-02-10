from kivy.config import Config
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '300')
import time
import os
import glob
from threading import Thread
from kivymd.app import MDApp
from kivy.clock import Clock
from data.inews_connection import generate_json
from data.s3_connection import upload_to_aws
from botocore.exceptions import NoCredentialsError


class ConsoleApp(MDApp):
    running = True
    counter = 0

    def start(self):
        self.running = True
        files = glob.glob('/Users/joseedwa/PycharmProjects/PiNews/data/story/*')
        for f in files:
            os.remove(f)
        if self.running:
            self.root.ids.confbox.text = ""
            self.cut_to_black()
            t = Thread(target=self.collect_rundown)
            t.daemon = True
            t.start()

    def stop(self):
        self.running = False
        self.counter = 0
        self.cut_to_black()
        self.countdown(10, 'stop')

    def collect_rundown(self):
        if self.running:
            self.root.ids.confbox.text = "RUNNING"
            self.root.ids.inewspulllbl.md_bg_color = 0.4, 0.960, 0.454, 1
            try:
                generate_json("CTS.TX.TC2_LW", "test_rundown")
                self.root.ids.inewsconflbl.md_bg_color = 0.4, 0.960, 0.454, 1
                t = Thread(target=self.gen_json)
                t.daemon = False
                t.start()
            except TimeoutError:
                print('WOBBLE WOBBLE WOBBLE WOBBLE ' + str(self.counter))
                self.root.ids.confbox.text = "FTP TIMEOUT - TRYING AGAIN"
                self.cut_to_black()
                self.start()

    def gen_json(self):
        if self.running:
            time.sleep(2)
            if self.running:
                self.root.ids.awspushlbl.md_bg_color = 0.4, 0.960, 0.454, 1
                try:
                    upload_to_aws('test_rundown.json', 'hero-cat-test', 'test_rundown')
                    time.sleep(5)
                    if self.running:
                        self.root.ids.awsconflbl.md_bg_color = 0.4, 0.960, 0.454, 1
                        self.counter += 1
                        self.root.ids.counter.text = str(self.counter)
                        Clock.schedule_once(lambda dt: self.countdown(10, 'repeat'), 0)
                except FileNotFoundError:
                    print('File not found')
                    self.root.ids.confbox.text = "FILE NOT FOUND - TRYING AGAIN"
                    self.start()
                except NoCredentialsError:
                    print("AWS Credentials error")
                    self.root.ids.confbox.text = "AWS CREDENTIALS ERROR - TRYING AGAIN"


    def countdown(self, num, cmd):
        if self.running:
            if cmd == 'repeat':
                self.root.ids.confbox.text = "SUCCESSFUL RUNDOWN TRANSFER INEWS > AWS. REPEATING IN " + str(num)
                if num == 0:
                    return self.start()
                num -= 1
                Clock.schedule_once(lambda dt: self.countdown(num, 'repeat'), 1)

        elif cmd == 'stop':
            self.root.ids.confbox.text = 'STOPPED - WAIT ' + str(num) + ' SECONDS BEFORE STARTING AGAIN'
            if num == 0:
                self.root.ids.confbox.text = 'STOPPED'
                return
            num -= 1
            Clock.schedule_once(lambda dt: self.countdown(num, 'stop'), 1)

    def cut_to_black(self):
        self.root.ids.inewspulllbl.md_bg_color = 0.819, 0.819, 0.819, 1
        self.root.ids.inewsconflbl.md_bg_color = 0.819, 0.819, 0.819, 1
        self.root.ids.awspushlbl.md_bg_color = 0.819, 0.819, 0.819, 1
        self.root.ids.awsconflbl.md_bg_color = 0.819, 0.819, 0.819, 1


if __name__ == '__main__':
    ConsoleApp().run()
