import discord
from discord.ext import commands
import os
import pickle
import member
import csv
import boto3
import glob
import io

#s3情報欄
accesckey = os.environ['KEY_ID']
secretkey = os.environ['SECRET_KEY_ID']
ragion = os.environ['REGION_NAME']

bucket_name = "hands-up0"

#discord情報欄
bot = commands.Bot(command_prefix='!')
token = os.environ['DISCORD_BOT_TOKEN']
s3 = boto3.client('s3',aws_access_key_id=accesckey,aws_secret_access_key=secretkey,region_name=ragion)

guild = {}

#s3からcsvファイルの取得
def get_s3file(bucket_name, key):
    s3 = boto3.resource('s3',aws_access_key_id=accesckey,aws_secret_access_key=secretkey,region_name=ragion)
    s3obj = s3.Object(bucket_name, key).get()
    return io.TextIOWrapper(io.BytesIO(s3obj['Body'].read()))

#csv作成
def create_csv(id,server):
    with open("./" + str(id) + ".csv","w",newline="") as f:
        writer = csv.writer(f)
        writer.writerow([id])
        for i in guild[id].time_key:
            if (len(guild[id].time[i].name) == 0) and (guild[id].time[i].tmp == 0):
                textout = [i] + [guild[id].time[i].tmp] + [str(x) for x in guild[id].time[i].n]
            elif guild[id].time[i].tmp == 0:
                textout = [i] + [guild[id].time[i].tmp] + [str(x) for x in guild[id].time[i].n] + [str(x) for x in guild[id].time[i].name]
            else:
                textout = [i] + [guild[id].time[i].tmp] + [str(x) for x in guild[id].time[i].n] + [str(x) for x in guild[id].time[i].name] + [str(x) for x in guild[id].time[i].res]
            writer.writerow(textout)
    pass

#csv読み込み
def read_csv(data):
    global guild
    id = int(data[0][0])
    guild[id] = member.guild()
    data.pop(0)
    #time_key作成
    for i in range(len(data)):
        c = ""
        rc = "" 
        time = data[i][0]
        guild[id].time[time] = member.menber(time+"@",6)
        data[i].pop(0)

        #挙手人数の取得
        if data[i][0] == "0":
            c = int(data[i][2])
            del data[i][0:3]
        elif data[i][0] == "1":
            c = int(data[i][2])
            rc = int(data[i][4])
            del data[i][0:6]
        
        #時間に挙手した人の復元
        #正挙手
        count = 6 - c
        for j in range(count):
            guild[id].time[time].add(data[i][j])
        if not rc == "":
            for j in range(rc):
                guild[id].time[time].reserve(data[i][j+count][1:])
    guild[id].time_key = sorted(guild[id].time.keys())

#s3にcsvのアップロード
def upload(id):
    cfile = "./" + str(id) + ".csv"
    s3.upload_file(cfile,bucket_name,cfile[2:])

#ボットにcsvの情報を読み込ませる
def download(id):
    data = []
    rec = csv.reader(get_s3file(bucket_name, str(id) + ".csv"))
    for row in rec:
        data.append(row)
    read_csv(data)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message(message):
    try:
        download(message.author.guild.id)
    except:
        pass
    if bot.user != message.author:
        #サーバー登録情報が無ければ自動登録
        if not message.author.guild.id in guild:
            guild[message.author.guild.id] = member.guild()
        await bot.process_commands(message)

# -------------------------------------------------------------------------------------------------------------
# コマンド関連
# -------------------------------------------------------------------------------------------------------------

### help表示
@bot.command()
async def hlp(ctx):
    await ctx.send(member.help())
# -------------------------------------------------------------------------------------------------------------

### メンション設定
@bot.command()
async def mention(ctx):
    await ctx.send(guild[ctx.author.guild.id].mentionset())
# -------------------------------------------------------------------------------------------------------------

### 交流戦時間登録
@bot.command()
async def set(ctx,*args):
    m = ""
    for i in args:
        #　登録するキーワードが10進で入力されているかどうか
        if  str.isdecimal(i): 
            guild[ctx.author.guild.id].set(str(i))
            # サーバーに時間の役職がすでにあるかどうか
            if discord.utils.get(ctx.guild.roles, name=str(i)) == None:
                await ctx.guild.create_role(name=str(i),mentionable = True)
            m = "```\n指定した交流戦の時間を追加登録しました\n```"
    if m == "":
        m = "```\n追加したい交流戦の時間を数値で入力してください\n```"
    await ctx.send(m)
    create_csv(ctx.author.guild.id,guild[ctx.author.guild.id])
# -------------------------------------------------------------------------------------------------------------

### 交流戦時間削除
@bot.command()
async def out(ctx,*args):
    for i in args:
        #　削除する時間が登録されているかどうか
        if i in guild[ctx.author.guild.id].time: 
            guild[ctx.author.guild.id].out(str(i))
            role = discord.utils.get(ctx.guild.roles, name=str(i))
            await role.delete()
            m = "```\n指定した交流戦の時間を削除しました\n```"
    if m == "":
        m = "```\n該当する交流戦の時間がありませんでした\n```"
    await ctx.send(m)
# -------------------------------------------------------------------------------------------------------------

### 挙手リセット
@bot.command()
async def clear(ctx):
    for i in guild[ctx.author.guild.id].time.keys():
        guild[ctx.author.guild.id].clear(str(i))
        #役職リセット
        role = discord.utils.get(ctx.guild.roles, name=str(i))
        await role.delete()
        await ctx.guild.create_role(name=str(i),mentionable = True)
    m = member.nowhands(guild[ctx.author.guild.id])
    await ctx.send(m)
    create_csv(ctx.author.guild.id,guild[ctx.author.guild.id])
# -------------------------------------------------------------------------------------------------------------

### 現在挙手状況表示
@bot.command()
async def now(ctx):
    await ctx.send(member.nowhands(guild[ctx.author.guild.id]))
# -------------------------------------------------------------------------------------------------------------

###　現在挙手状況メンション付き表示
@bot.command()
async def mnow(ctx):
    guild[ctx.author.guild.id].mention = 1
    await ctx.channel.send(member.nowhands(guild[ctx.author.guild.id]))
# -------------------------------------------------------------------------------------------------------------

### 挙手
@bot.command()
async def c(ctx,*args):
    # 他人の操作をしようとしたとき、「player」変数に格納
    if (len(args) > 1) and (args[0][:2] == "<@"):
        id = int(args[0][3:21])
        player = ctx.author.guild.get_member(id)

    # 他人の追加
    if (args[0][:2] == "<@"):
        m = player.name + "さんの挙手を追加します"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not player.name in guild[ctx.author.guild.id].time[i].name:
                    # 仮挙手をしていた場合仮挙手を削除
                    if "仮" + player.name in guild[ctx.author.guild.id].time[i].res:
                        guild[ctx.author.guild.id].time[i].reservedel(player.name)
                    guild[ctx.author.guild.id].time[i].add(player.name)
                    # 挙手した時間が@3以下だったらメンション付きにする
                    if len(guild[ctx.author.guild.id].time[i].name) >= 3:
                        guild[ctx.author.guild.id].mention = 1
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await player.add_roles(role)
    # 自分の追加
    else:
        m = ctx.author.name + "さんの挙手を確認しました"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not ctx.author.name in guild[ctx.author.guild.id].time[i].name:
                    # 仮挙手をしていた場合仮挙手を削除
                    if "仮" + ctx.author.name in guild[ctx.author.guild.id].time[i].res:
                        guild[ctx.author.guild.id].time[i].reservedel(ctx.author.name)
                    guild[ctx.author.guild.id].time[i].add(ctx.author.name)
                    # 挙手した時間が@3以下だったらメンション付きにする
                    if len(guild[ctx.author.guild.id].time[i].name) >= 3:
                        guild[ctx.author.guild.id].mention = 1
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await ctx.author.add_roles(role)
    # 変更後の挙手状態を表示
    await ctx.send(member.nowhands(guild[ctx.author.guild.id]))
    create_csv(ctx.author.guild.id,guild[ctx.author.guild.id])
    upload(ctx.author.guild.id)
    # -------------------------------------------------------------------------------------------------------------

### 仮挙手
@bot.command()
async def rc(ctx,*args):
    # 他人の操作をしようとしたとき
    if (len(args) > 1) and (args[0][:2] == "<@"):
        id = int(args[0][3:21])
        player = ctx.author.guild.get_member(id)

    # 他人の追加
    if (args[0][:2] == "<@"):
        m = player.name + "さんの仮挙手を追加します"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not player.name in guild[ctx.author.guild.id].time[i].res:
                    # 挙手をしていた場合挙手を削除
                    if player.name in guild[ctx.author.guild.id].time[i].name:
                        guild[ctx.author.guild.id].time[i].sub(player.name)
                    guild[ctx.author.guild.id].time[i].reserve(player.name)
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await player.add_roles(role)
    # 自分の追加
    else:
        m = ctx.author.name + "さんの仮挙手を確認しました"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not ctx.author.name in guild[ctx.author.guild.id].time[i].res:
                    # 挙手をしていた場合挙手を削除
                    if ctx.author.name in guild[ctx.author.guild.id].time[i].name:
                        guild[ctx.author.guild.id].time[i].sub(ctx.author.name)
                    guild[ctx.author.guild.id].time[i].reserve(ctx.author.name)
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await ctx.author.add_roles(role)
    # 変更後の挙手状態を表示
    await ctx.send(member.nowhands(guild[ctx.author.guild.id]))
    create_csv(ctx.author.guild.id,guild[ctx.author.guild.id])
    upload(ctx.author.guild.id)
# -------------------------------------------------------------------------------------------------------------

### 挙手取り下げ
@bot.command()
async def d(ctx,*args):
    # 他人の操作をしようとしたとき
    if (len(args) > 1) and (args[0][:2] == "<@"):
        id = int(args[0][3:21])
        player = ctx.author.guild.get_member(id)

    # 他人の追加
    if (args[0][:2] == "<@"):
        m = player.name + "さんの挙手を取り下げます"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                guild[ctx.author.guild.id].time[i].sub(player.name)
                role = discord.utils.get(ctx.guild.roles, name=str(i))
                await player.remove_roles(role)

    #自分の追加
    else:
        m = ctx.author.name + "さんの挙手取り下げを確認しました"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                guild[ctx.author.guild.id].time[i].sub(ctx.author.name)
                role = discord.utils.get(ctx.guild.roles, name=str(i))
                await ctx.author.remove_roles(role)
    # 変更後の挙手状態を表示
    await ctx.send(member.nowhands(guild[ctx.author.guild.id]))
    create_csv(ctx.author.guild.id,guild[ctx.author.guild.id])
    upload(ctx.author.guild.id)
# -------------------------------------------------------------------------------------------------------------

### 仮挙手取り下げ
@bot.command()
async def rd(ctx,*args):
    # 他人の操作をしようとしたとき
    if (len(args) > 1) and (args[0][:2] == "<@"):
        id = int(args[0][3:21])
        player = ctx.author.guild.get_member(id)

    if (args[0][:2] == "<@"):
        m = player.name + "さんの仮挙手を取り下げます"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                guild[ctx.author.guild.id].time[i].reservedel(player.name)
                role = discord.utils.get(ctx.guild.roles, name=str(i))
                await player.remove_roles(role)

    #自分の追加
    else:
        m = ctx.author.name + "さんの仮挙手取り下げを確認しました"
        await ctx.send(m)
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                guild[ctx.author.guild.id].time[i].reservedel(ctx.author.name)
                role = discord.utils.get(ctx.guild.roles, name=str(i))
                await ctx.author.remove_roles(role)
    # 変更後の挙手状態を表示
    await ctx.send(member.nowhands(guild[ctx.author.guild.id]))
    create_csv(ctx.author.guild.id,guild[ctx.author.guild.id])
    upload(ctx.author.guild.id)
# -------------------------------------------------------------------------------------------------------------

### 交流戦呼びかけ
@bot.command()
async def vs(ctx,*args):
    # args = [時間,対戦相手,フレンドコード,開設時間]
    if (len(args) != 4) or (len(args[2]) != 14) or (str.isdecimal(args[0]) == False):
        return
    time = args[0]
    role = discord.utils.get(ctx.guild.roles, name=str(time))
    vsclan = args[1]
    fc = args[2]
    op = args[3]

    await ctx.send(member.vs(role.mention,vsclan,fc,op))
# -------------------------------------------------------------------------------------------------------------

bot.run(token)
