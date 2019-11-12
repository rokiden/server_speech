from argparse import ArgumentParser
import os
import time
from win10toast import ToastNotifier
from server_speech import ServerSpeechClient


class Watcher:
    def __init__(self, path, poll, search, toast_phrase="Quartus Done!", speech_ip=None, speech_port=1488,
                 speech_phrase="Quartus Done!", speech_lang='en'):
        self.search = search
        self.poll = poll
        self.path = path
        self.toast_phrase = toast_phrase
        if speech_ip is not None:
            self.speech_client = ServerSpeechClient(speech_ip, speech_port)
        else:
            self.speech_client = None
        self.speech_phrase = speech_phrase
        self.speech_lang = speech_lang
        self.toaster = ToastNotifier()

    def notify(self, file):
        print('notify', file)
        self.toaster.show_toast(self.toast_phrase,
                                file,
                                duration=5,
                                threaded=True)
        if self.speech_client is not None:
            self.speech_client.send(self.speech_phrase, self.speech_lang)

    def search_targets(self, postfix='.done'):
        # print('search_targets')
        files = os.listdir(self.path)
        targets = []
        for f in files:
            if f.endswith(postfix):
                targets.append(self.path + '\\' + f)
        return targets

    def check_targets(self, times, first):
        # print('check_targets')
        delete = []
        for file in times:
            try:
                new_time = os.stat(file).st_mtime
                if times[file] is None or times[file] != new_time:
                    times[file] = new_time
                    if not first:
                        self.notify(file)
            except FileNotFoundError:
                delete.append(file)
                print('deleted', file)
        for d in delete:
            del times[d]

    def watch(self):
        first = True
        search_cntr = 0
        times = {}

        try:
            while True:
                if search_cntr == 0:
                    search_cntr = self.search
                    targets = self.search_targets()
                    if first:
                        print(targets)
                    for t in targets:
                        if t not in times:
                            times[t] = None
                self.check_targets(times, first)
                first = False
                if search_cntr > 0:
                    search_cntr -= 1
                time.sleep(self.poll)
        except KeyboardInterrupt:
            print('exit')


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('path', metavar='PATH', help='path to Quartus project output folder')
    argparser.add_argument("--poll", metavar='SEC', help="polling period", default=3)
    argparser.add_argument("--search", metavar='POLLS', help="new targets search period, poll periods", default=4)
    argparser.add_argument("--ss-ip", metavar='IP', help="ServerSpeech ip")
    argparser.add_argument("--ss-phrase", metavar='PHRASE', help="ServerSpeech phrase", default='Quartus done')
    argparser.add_argument("--ss-lang", metavar='LANG', help="ServerSpeech lang", default='en')
    args = argparser.parse_args()

    print(args)

    w = Watcher(args.path, args.poll, args.search, speech_ip=args.ss_ip, speech_phrase=args.ss_phrase,
                speech_lang=args.ss_lang)
    w.watch()
