import logging

LOGGING_LEVEL = logging.DEBUG

class myLogger():
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOGGING_LEVEL)
        self.logger.addHandler(self.makeStreamHandler())

    def makeStreamHandler(self):
        ch = logging.StreamHandler()
        ch.setLevel(LOGGING_LEVEL)
        ch.setFormatter(self.createFormatter())
        return ch

    def createFormatter(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return formatter



if __name__ == "__main__":
    logger = myLogger()
    logger.logger.debug('debug message')