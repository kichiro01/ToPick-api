
from enum import Enum

class ReportReasons(Enum):
    SPAM = ('001', '商業目的、スパム')
    PERSONAL_INFO = ('002', '個人情報を含む')
    SENSITIVE = ('003', 'センシティブなコンテンツ（暴力、露骨な性的表現等）')
    SLANDER = ('004', '誹謗中傷')
    AGITATION = ('005', 'テロリズムや自殺・自傷行為の扇動、助長')
    RUMOR = ('006', '誤った情報、デマ')
    OTHERS = ('099', 'その他')

    def __init__(self, code, title):
        self.code = code
        self.title = title
    
    @classmethod
    def members_as_list(cls):
        # Order dictionary -> list
        return [*cls.__members__.values()]
    
    @classmethod
    def getTitleFromCode(cls, code):
        for c in cls.members_as_list():
            if code == c.code:
                return c.title
        # default
        return ReportReasons.OTHERS.title