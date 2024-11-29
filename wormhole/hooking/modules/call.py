from .base import BaseModule
import pyaudio

CHUNK = 1024


class Call(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        # LIVE
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=pyaudio.paInt32,
            channels=1,
            rate=16000,
            output=True
        )

        # TO FILE
        #try:
        #    os.unlink('/tmp/call')
        #except:
        #    pass
        #self.wf = wave.open('/tmp/call', 'wb')
        #self.wf.setnchannels(1)
        #self.wf.setsampwidth(pyaudio.paInt16)
        #self.wf.setframerate(16000)

    def _process(self):
        self.stream.write(self.message.data)

        #self.wf.writeframes(self.message.data)


