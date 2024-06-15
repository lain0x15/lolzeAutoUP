from src.lolzeAutoUP import lolzeAutoUP
from pathlib import Path
if __name__ == "__main__":
    baseDir = Path(__file__).parent
    bot = lolzeAutoUP (configFilePath = baseDir / "config.json", tmpFolderPath = baseDir / 'files/tmp',  modulesPath = baseDir / 'src/modules')
    bot.run()
