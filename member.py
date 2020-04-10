class menber:
    def __init__(self,text,num): # 初期化： インスタンス作成時に自動的に呼ばれる
        self.n = [text,num]
        self.name = []
        self.res = []
        self.resn =["(",0,")"]
        self.tmp = 0
    
    def add(self,name):
        if(self.n[1] > 0):
            self.n[1] -= 1
            if self.tmp == 1:
                self.n[3] -= 1
            self.name.append(name)
    
    def reserve(self,name):
        if len(self.res) == 0:
            self.tmp = 1
            self.res.append("仮" + name)
            self.resn[1] += 1
            for i in range(3):
                self.n.insert(2+i,self.resn[i])
        else:
            self.res.append("仮" + name)
            self.n[3] += 1

    def sub(self,name):
        for i in range(len(self.name)):
            if self.name[i] == name:
                self.name.pop(i)
                self.n[1] += 1
                break

    def reservedel(self,name):
        for i in range(len(self.res)):
            if self.res[i] == "仮" + name:
                self.res.pop(i)
                self.n[3] -= 1
                break
        if len(self.res) == 0:
            self.tmp = 0
            for i in range(3):
                self.n.pop(2)

class guild:
    def __init__(self):
        self.mention = 0
        self.time = {}
        self.time_key = []
    
    def set(self,time):
        send = time + "@"
        self.time[time] = menber(send,6)
        self.time_key = sorted(self.time.keys())

    def out(self,time):
        del self.time[time]
        self.time_key = sorted(self.time.keys())

    def clear(self,time):
        send = time + "@"
        self.time[time] = menber(send,6)
    
    def mentionset(self):
        if self.mention == 1:
            self.mention = 0
            m = "```mention設定をOFFにしました```"
            return m
        else:
            self.mention = 1
            m = "```mention設定をONにしました```"
            return m

def nowhands(server):
    if len(server.time_key) == 0:
        m = "```\n" \
            + "交流戦の時間が登録されていません\n" \
            + "```"
    else:
        if server.mention == 1:
            mall = "@everyone\n"
        else:
            mall = "\n"
        mwar = "**WAR LIST**\n"
        mtmp = ""
        for i in server.time_key:
            if server.time[i].tmp == 1:
                mtmp = mtmp + "".join(str(x) for x in server.time[i].n) + " " + ",".join(str(x) for x in server.time[i].name) + " " + ",".join(str(x) for x in server.time[i].res) + "\n"
            else:
                mtmp = mtmp + "".join(str(x) for x in server.time[i].n) + " " + ",".join(str(x) for x in server.time[i].name) + "\n"
        m = mall + mwar + "```" + mtmp + "```"
    return m

def help():
    m = "```\n" \
    + "コマンド一覧\n" \
\
    + "!mention -> mentionの設定\n" \
        + "   挙手リストを表示するときの@everyoneの有無を設定します\n" \
        + "\n" \
\
    + "!set -> 交流戦時間の追加\n" \
        + "   例:!set 21 22 23 -> 21~23時の交流戦時間を追加する\n" \
        + "\n" \
\
    + "!out -> 交流戦時間の削除\n" \
        + "   例:!out 21 22 23 -> 21~23時の交流戦時間を削除する\n" \
        + "\n" \
\
    + "!c -> 挙手\n" \
        + "   例:!c 21      -> 21時に自分が追加される\n" \
        + "      !c @non 21 -> 21時にnonが追加される\n" \
        + "\n" \
\
    +"!rc -> 仮挙手\n" \
        + "   例:!rc 21      -> 21時に自分が仮で追加される\n" \
        + "      !rc @non 21 -> 21時にnonが仮で追加される\n" \
        + "\n" \
\
    + "!d -> 挙手取り下げ\n" \
        + "   例:!d 21      -> 21時の自分の挙手を取り下げる\n" \
        + "      !d @non 21 -> 21時のnonの挙手を取り下げる\n" \
        + "\n" \
\
    + "!rd -> 仮挙手取り下げ\n" \
        + "   例:!rd 21      -> 21時の自分の仮挙手を取り下げる\n" \
        + "      !rd @non 21 -> 21時のnonの仮挙手を取り下げる\n" \
        + "\n" \
\
    + "!now -> 現在の挙手状況の確認\n" \
        + "\n" \
\
    + "!clear -> 挙手リセット\n" \
    + "```"

    return m
