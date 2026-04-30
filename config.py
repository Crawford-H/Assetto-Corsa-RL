from dotenv import dotenv_values


class Config:
    def __init__(self):
        vars = dotenv_values(".env")
        self.AC_PATH: str = str(vars["AC_PATH"])
        self.AC_CFG_PATH: str = str(vars["AC_CFG_PATH"])
        self.BASE_PATH: str = str(vars["BASE_PATH"])
        self.OUT_PATH: str = str(vars["OUT_PATH"])


config = Config()
