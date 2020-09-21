import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import os
import pickle
import member
import csv
import boto3
import glob
import io
import gspread #$ pip install gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import random
import traceback

######################################################################################################################
#スプレッドシート情報欄
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('test-python-275700-5f70ae0934df.json', scope)
gc = gspread.authorize(credentials)
# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - 
### ラウンジレート
SPREADSHEET_KEY = "12Cj_4jIfdL8MQdrBLZEGPgwc4x_a6cphNg_PsNR0gxM"
wkb = gc.open_by_key(SPREADSHEET_KEY)
wks = wkb.sheet1
# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - 
### 挙手経験値シート
SPSHEET_KEY = "1s5ApIPhLL8xS1s2OokhBf3ycbgE6Wrow1Lc8cgxxENY"
EXP = gc.open_by_key(SPSHEET_KEY)
personal = EXP.worksheet("個人経験値")
team = EXP.worksheet("チーム経験値")
show = EXP.worksheet("personal_data")
# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - 
######################################################################################################################

#s3情報欄
accesckey = os.environ['KEY_ID']
secretkey = os.environ['SECRET_KEY_ID']
ragion = os.environ['REGION_NAME']

bucket_name = "hands-up0"

#discord情報欄
bot = commands.Bot(command_prefix='!')
bot.remove_command("help")
token = os.environ['DISCORD_BOT_TOKEN']
s3 = boto3.client('s3',aws_access_key_id=accesckey,aws_secret_access_key=secretkey,region_name=ragion)

guild = {}

image = {"iron":"https://cdn.discordapp.com/attachments/736282187770363976/743528091858763786/iron_s32.png",
        "bronze":"https://cdn.discordapp.com/attachments/736282187770363976/743528106526113884/bronze_s3.png",
        "silver":"https://cdn.discordapp.com/attachments/736282187770363976/743528159391121478/silver_s3.png",
        "gold":"https://cdn.discordapp.com/attachments/736282187770363976/743528125127983124/gold_s3.png",
        "platinum":"https://cdn.discordapp.com/attachments/736282187770363976/743528185731481662/platinum2.png",
        "sapphire":"https://cdn.discordapp.com/attachments/736282187770363976/743528240232267936/sapphire_s3.png",
        "diamond":"https://cdn.discordapp.com/attachments/736282187770363976/743528221923999924/diamonds3maybe.png",
        "master":"https://cdn.discordapp.com/attachments/736282187770363976/743528268497682452/master_s32.png"}

#s3からcsvファイルの取得
def get_s3file(bucket_name, key):
    s3 = boto3.resource('s3',aws_access_key_id=accesckey,aws_secret_access_key=secretkey,region_name=ragion)
    s3obj = s3.Object(bucket_name, key).get()
    return io.TextIOWrapper(io.BytesIO(s3obj['Body'].read()))

#csv作成
def create_csv(id,server,name,msg):
    with open("/tmp/" + str(id) + ".csv","w",newline="") as f:
        writer = csv.writer(f)
        writer.writerow([id,str(guild[id].mentionnum),name,msg])
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
    if len(data[0]) > 1:
        guild[id].mentionnum = int(data[0][1])
        if len(data[0]) > 3:
            guild[id].msg = int(data[0][3])
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
                guild[id].time[time].reserve(data[i][j+count])
    guild[id].time_key = sorted(guild[id].time.keys())

#s3にcsvのアップロード
def upload(id):
    cfile = "/tmp/" + str(id) + ".csv"
    s3.upload_file(cfile,bucket_name,cfile[5:])

#ボットにcsvの情報を読み込ませる
def download(id):
    data = []
    rec = csv.reader(get_s3file(bucket_name, str(id) + ".csv"))
    for row in rec:
        data.append(row)
    read_csv(data)

#ラウンジデータ取得
def get_List(name):
    Player = wks.range("C2:C3600")
    count = 0
    for i in Player:
        count += 1
        if i.value.lower() == name.lower():
            data = wks.range("B" + str(count+1) + ":K" + str(count+1))
            return data

#mmr取得
def get_mmr(name):
    Player = wks.range("C2:C3600")
    count = 0
    for i in Player:
        count += 1
        if i.value.lower() == name.lower():
            mmr = wks.cell(count+1,4).value
            return mmr

#ランク判定
def judge(mmr):
    if mmr <=1999:
        return "iron",0x6c6a6a
    elif 2000 <= mmr <= 3499:
        return "bronze",0xe17319
    elif 3500 <= mmr <= 4999:
        return "silver",0xd1e1dc
    elif 5000 <= mmr <= 6499:
        return "gold",0xdee114
    elif 6500 <= mmr <= 7999:
        return "platinum",0x2bd7ee
    elif 8000 <= mmr <= 9499:
        return "sapphire",0x2b5bee
    elif 9500 <= mmr <= 10999:
        return "diamond",0xbee7f9
    elif 11000 <= mmr <= 12499:
        return "master",0x000000
    elif mmr <= 12500:
        return "grandmaster",0x000000

def guild_csv(name,ID,Owner):
    with open("/tmp/" + "server list" + ".csv","w",newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name","ID","Oewner"])
        for i in range(len(name)):
            writer.writerow([name[i],ID[i],Owner[i]])
    cfile = "/tmp/" + "server list" + ".csv"
    s3.upload_file(cfile,bucket_name,cfile[5:])

#経験値書込み(個人)
def exp_run_p(ctx,counter):
    for user in counter:
        all_cell = personal.range("A2:V1000")
        user_id = []
        for i in range(len(all_cell) // 22):
            user_id.append(all_cell[i * 22:(i+1)*22])
        for row , i in enumerate(user_id,1):
            if i[1].value == "":
                i[0].value = user.name
                i[1].value = str(user.id)
                i[2].value = str(ctx.guild.id)
                i[3].value = counter[user]
                break
            elif str(user.id) == i[1].value:
                for col , j in enumerate(i,1):
                    if j.value == "":
                        j.value = str(ctx.guild.id)
                        i[col].value = counter[user]
                        break
                    elif str(ctx.guild.id) == j.value:
                        j.value = int(j.value) + counter(user)
                        break
                break
        write_cells = []
        for cells in user_id:
            write_cells.extend(cells)
        personal.update_cells(write_cells)
                    
#経験値書込み(チーム)
def exp_run_t(ctx):
    team_id = team.range("B2:B1000")
    count = 0
    for i in team_id:
        count += 1
        if i.value == "":
            team.update_cell(count+1,2,str(ctx.guild.id))
            break
        else:
            break

#経験値計算
def get_exp(ctx,reg):
    counter = {}
    #詳細吸出し
    for i in reg:
        for j in i:    
            if j[:1] == "補" or j[:1] == "仮":
                P = j[1:]
                n = 1
            else:
                P = j
                n = 2
            name = ctx.guild.get_member_named(P)
            if name == None:
                pass
            else:
                if name in counter:
                    counter[name] += n
                else:
                    counter[name] = n
    #
    exp_run_p(ctx,counter)
    exp_run_t(ctx)

#error
async def debug(ctx,mes):
    ch = 732076771796713492
    embed = discord.Embed(title="エラー情報", description="", color=0xf00)
    embed.add_field(name="エラー発生サーバー名", value=ctx.guild.name, inline=False)
    embed.add_field(name="エラー発生サーバーID", value=ctx.guild.id, inline=False)
    embed.add_field(name="エラー発生ユーザー名", value=ctx.author.name, inline=False)
    embed.add_field(name="エラー発生ユーザーID", value=ctx.author.id, inline=False)
    embed.add_field(name="エラー発生コマンド", value=ctx.message.content, inline=False)
    embed.add_field(name="発生エラー", value=mes, inline=False)
    m = await bot.get_channel(ch).send(embed=embed)
    await ctx.send("何らかのエラーが発生しました。ごめんなさい。\n"\
        +f"このエラーについて問い合わせるときはこのコードも一緒にお知らせください：{m.id}\n"\
        +"***連絡先***\n"\
        +"***Twitter*** : __@enoooooooon__\n"\
        +"***Discord*** : __non#0831__")

@bot.event
async def on_ready():
    guilds = bot.guilds
    num = len(guilds)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(num)+"servers"))

@bot.event
async def on_guild_join(guild):
    CHANNEL_ID = 744741657769148457
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(guild.name + "に導入されました\n" + "代表者は" + str(guild.owner) + "です。")
    guilds = bot.guilds
    num = len(guilds)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(num)+"servers"))

@bot.event
async def on_guild_remove(guild):
    CHANNEL_ID = 744741657769148457
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(guild.name + "から削除されました")
    guilds = bot.guilds
    li = ""
    for i in guilds:
        li += i.name + " : " + str(i.owner) +"\n"
    await channel.send(li)
    num = len(guilds)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(num)+"servers"))

@bot.event
async def on_message(message):
    try:
        if not message.author.guild.id in guild:
            download(message.author.guild.id)
    except:
        pass
    if bot.user != message.author:
        #サーバー登録情報が無ければ自動登録
        if not message.author.guild.id in guild:
            guild[message.author.guild.id] = member.guild()
        await bot.process_commands(message)
 
@bot.event
async def on_command_error(ctx, error):
    if not isinstance(error, CommandNotFound):
        pass
# -------------------------------------------------------------------------------------------------------------
# コマンド関連
# -------------------------------------------------------------------------------------------------------------

### help表示
@bot.command()
async def help(ctx):
    try:
        await ctx.send(embed=member.help())
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 交流戦時間登録
@bot.command()
async def set(ctx,*args):
    try:
        m = ""
        for i in args:
            #　登録するキーワードが10進で入力されているかどうか
            if  str.isdecimal(i[:2]): 
                guild[ctx.author.guild.id].set(str(i))
                # サーバーに時間の役職がすでにあるかどうか
                if discord.utils.get(ctx.guild.roles, name=str(i)) == None:
                    await ctx.guild.create_role(name=str(i),mentionable = True)
                m = "```\n指定した交流戦の時間を追加登録しました\n```"
        if m == "":
            m = "```\n追加したい交流戦の時間を数値で入力してください\n```"
        await ctx.send(m)
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 交流戦時間削除
@bot.command()
async def out(ctx,*args):
    try:
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
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 挙手リセット
@bot.command()
async def clear(ctx):
    try:
        reg = []
        for i in guild[ctx.author.guild.id].time.keys():
            Players = guild[ctx.author.guild.id].time[i].name + guild[ctx.author.guild.id].time[i].res
            reg.append(Players)
            guild[ctx.author.guild.id].clear(str(i))
            #役職リセット
            role = discord.utils.get(ctx.guild.roles, name=str(i))
            await role.delete()
            await ctx.guild.create_role(name=str(i),mentionable = True)
        m , embed = member.nowhands(guild[ctx.author.guild.id])
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
        get_exp(ctx,reg)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 現在挙手状況表示
@bot.command()
async def now(ctx):
    try:
        m , embed = member.nowhands(guild[ctx.author.guild.id])
        if guild[ctx.author.guild.id].msg == "":
            pass
        else:
            try:
                guild[ctx.author.guild.id].msg = await ctx.fetch_message(guild[ctx.author.guild.id].msg)
                await guild[ctx.author.guild.id].msg.delete()
            except:
                pass
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

###　現在挙手状況メンション付き表示
@bot.command()
async def mnow(ctx):
    try:
        guild[ctx.author.guild.id].mention = 1
        m , embed = member.nowhands(guild[ctx.author.guild.id])
        if guild[ctx.author.guild.id].msg == "":
            pass
        else:
            try:
                guild[ctx.author.guild.id].msg = await ctx.fetch_message(guild[ctx.author.guild.id].msg)
                await guild[ctx.author.guild.id].msg.delete()
            except:
                pass
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 挙手
@bot.command()
async def c(ctx,*args):
    try:
        # 他人の操作をしようとしたとき、「player」変数に格納
        if (len(args) > 1) and (args[0][:2] == "<@"):
            id_sub = args[0].translate(str.maketrans({"<":"","@":"",">":"","!":""}))
            id = int(id_sub)
            player = ctx.author.guild.get_member(id)
            m = player.name + "さんの挙手を追加します"
        else:
            player = ctx.author
            m = player.name + "さんの挙手を確認しました"

        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not player.name in guild[ctx.author.guild.id].time[i].name:
                    # 仮挙手をしていた場合仮挙手を削除
                    if "仮" + player.name in guild[ctx.author.guild.id].time[i].res:
                        guild[ctx.author.guild.id].time[i].reservedel("仮" + player.name)
                    # 補欠挙手をしていた場合挙手を削除
                    if "補" + player.name in guild[ctx.author.guild.id].time[i].res:
                        guild[ctx.author.guild.id].time[i].reservedel("補" + player.name)
                    if len(guild[ctx.author.guild.id].time[i].name) == 6:
                        guild[ctx.author.guild.id].time[i].reserve("補" + player.name)
                    else:
                        guild[ctx.author.guild.id].time[i].add(player.name)
                    # 挙手した時間が@3以下だったらメンション付きにする
                    if 6 - len(guild[ctx.author.guild.id].time[i].name) <= guild[ctx.author.guild.id].mentionnum:
                        guild[ctx.author.guild.id].mention = 1
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await player.add_roles(role)
        # 変更後の挙手状態を表示
        m2 , embed = member.nowhands(guild[ctx.author.guild.id])
        m = m2 + m 
        if guild[ctx.author.guild.id].msg == "":
            pass
        else:
            try:
                guild[ctx.author.guild.id].msg = await ctx.fetch_message(guild[ctx.author.guild.id].msg)
                await guild[ctx.author.guild.id].msg.delete()
            except:
                pass
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 仮挙手
@bot.command()
async def rc(ctx,*args):
    try:
        # 他人の操作をしようとしたとき、「player」変数に格納
        if (len(args) > 1) and (args[0][:2] == "<@"):
            id_sub = args[0].translate(str.maketrans({"<":"","@":"",">":"","!":""}))
            id = int(id_sub)
            player = ctx.author.guild.get_member(id)
            m = player.name + "さんの仮挙手を追加します"
        else:
            player = ctx.author
            m = player.name + "さんの仮挙手を確認しました"

        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not player.name in guild[ctx.author.guild.id].time[i].res:
                    # 挙手をしていた場合挙手を削除
                    if player.name in guild[ctx.author.guild.id].time[i].name:
                        guild[ctx.author.guild.id].time[i].sub(player.name)
                    # 補欠挙手をしていた場合挙手を削除
                    if "補" + player.name in guild[ctx.author.guild.id].time[i].res:
                        guild[ctx.author.guild.id].time[i].reservedel("補" + player.name)
                    guild[ctx.author.guild.id].time[i].reserve("仮" + player.name)
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await player.add_roles(role)
        # 変更後の挙手状態を表示
        m2 , embed = member.nowhands(guild[ctx.author.guild.id])
        m = m2 + m 
        if guild[ctx.author.guild.id].msg == "":
            pass
        else:
            try:
                guild[ctx.author.guild.id].msg = await ctx.fetch_message(guild[ctx.author.guild.id].msg)
                await guild[ctx.author.guild.id].msg.delete()
            except:
                pass
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 補欠挙手
@bot.command()
async def s(ctx,*args):
    try:
        # 他人の操作をしようとしたとき、「player」変数に格納
        if (len(args) > 1) and (args[0][:2] == "<@"):
            id_sub = args[0].translate(str.maketrans({"<":"","@":"",">":"","!":""}))
            id = int(id_sub)
            player = ctx.author.guild.get_member(id)
            m = player.name + "さんの補欠挙手を追加します"
        else:
            player = ctx.author
            m = player.name + "さんの補欠挙手を確認しました"

        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                # 指定した時間にすでに挙手をしているか
                if not player.name in guild[ctx.author.guild.id].time[i].res:
                    # 挙手をしていた場合挙手を削除
                    if player.name in guild[ctx.author.guild.id].time[i].name:
                        guild[ctx.author.guild.id].time[i].sub(player.name)
                    # 仮挙手をしていた場合挙手を削除
                    if "仮" + player.name in guild[ctx.author.guild.id].time[i].res:
                        guild[ctx.author.guild.id].time[i].reservedel("仮" + player.name)
                    guild[ctx.author.guild.id].time[i].reserve("補" + player.name)
                    role = discord.utils.get(ctx.guild.roles, name=str(i))
                    await player.add_roles(role)
        # 変更後の挙手状態を表示
        m2 , embed = member.nowhands(guild[ctx.author.guild.id])
        m = m2 + m 
        if guild[ctx.author.guild.id].msg == "":
            pass
        else:
            try:
                guild[ctx.author.guild.id].msg = await ctx.fetch_message(guild[ctx.author.guild.id].msg)
                await guild[ctx.author.guild.id].msg.delete()
            except:
                pass
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### 挙手取り下げ
@bot.command()
async def d(ctx,*args):
    try:
        # 他人の操作をしようとしたとき、「player」変数に格納
        if (len(args) > 1) and (args[0][:2] == "<@"):
            id_sub = args[0].translate(str.maketrans({"<":"","@":"",">":"","!":""}))
            id = int(id_sub)
            player = ctx.author.guild.get_member(id)
            m = player.name + "さんの挙手を取り下げます"
        else:
            player = ctx.author
            m = player.name + "さんの挙手取り下げを確認しました"

        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                role = discord.utils.get(ctx.guild.roles, name=str(i))
                # 挙手をしていた場合挙手を削除
                if player.name in guild[ctx.author.guild.id].time[i].name:
                    guild[ctx.author.guild.id].time[i].sub(player.name)
                # 仮挙手をしていた場合挙手を削除
                if "仮" + player.name in guild[ctx.author.guild.id].time[i].res:
                    guild[ctx.author.guild.id].time[i].reservedel("仮" + player.name)
                # 補欠挙手をしていた場合挙手を削除
                if "補" + player.name in guild[ctx.author.guild.id].time[i].res:
                    guild[ctx.author.guild.id].time[i].reservedel("補" + player.name)
                await player.remove_roles(role)
        # 変更後の挙手状態を表示
        m2 , embed = member.nowhands(guild[ctx.author.guild.id])
        m = m2 + m 
        if guild[ctx.author.guild.id].msg == "":
            pass
        else:
            try:
                guild[ctx.author.guild.id].msg = await ctx.fetch_message(guild[ctx.author.guild.id].msg)
                await guild[ctx.author.guild.id].msg.delete()
            except:
                pass
        guild[ctx.author.guild.id].msg = await ctx.send(content=m,embed=embed)
        guild[ctx.author.guild.id].msg = guild[ctx.author.guild.id].msg.id
        create_csv(ctx.author.guild.id,guild[ctx.author.guild.id],ctx.author.guild.name,guild[ctx.author.guild.id].msg)
        upload(ctx.author.guild.id)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### mention人数設定
@bot.command()
async def ch(ctx,*args):
    try:
        for i in args:
            if i == "-1":
                m = "```mention設定をOFFにしました\n```"
                guild[ctx.author.guild.id].mentionnum = -1
                break
            if  str.isdecimal(i):
                if int(i) > 6:
                    m = "```5以下で設定してください\n```"
                else:
                    guild[ctx.author.guild.id].mentionnum = int(i)
                    m = "```\nmentionを送る人数を@" + str(i) + "人に変更しました\n```"
            else:
                m = "```\n数値で入力してください\n```"
        await ctx.channel.send(m)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------
### stats表示
@bot.command()
async def stats(ctx,*args):
    try:
        if len(args) == 0:
            await ctx.send("```please type 「!stats (Player name in Lounge)」```")
        else:
            await ctx.send("```please type 「!exp team」or「!exp player」```")
            title = wks.range("B1:K1")
            name = " ".join(args)
            data = get_List(name)
            if data == None:
                embed=discord.Embed(title="Stats",description=name ,color=0xee1111)
                embed.add_field(name="Stats Data", value="None", inline=True)
            else:
                ot = [i.value for i in title]
                out = [i.value for i in data]
                img,color = judge(int(out[2]))
                embed=discord.Embed(title="Stats",description=data[1].value ,color=color)
                embed.set_thumbnail(url=image[img])
                for i in range(len(ot)):
                    if i != 1:
                        embed.add_field(name=ot[i], value=out[i], inline=True)
            msg = await ctx.send(embed=embed)
            #await asyncio.sleep(20)
            #await msg.delete()
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

### mmr表示
@bot.command()
async def mmr(ctx,*args):
    try:
        if len(args) == 0:
            await ctx.send("```please type 「!mmr (Player name in Lounge)」```")
        else:
            names = name = " ".join(args)
            name = names.split(",")
            embed=discord.Embed(title="MMR",color=0x000000)
            for i in name:
                mmr = get_mmr(i)
                embed.add_field(name=i,value=mmr,inline=False)
            await ctx.send(embed=embed)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

###guild list表示
@bot.command()
async def admin(ctx,*args):
    try:
        if ctx.author.id == 246138083299295235:
            guilds = bot.guilds
            name = []
            ID = []
            Owner = []
            for i in guilds:
                name.append(i.name)
                ID.append(str(i.id))
                Owner.append(str(i.owner))
            guild_csv(name,ID,Owner)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

###外交選出
@bot.command()
async def pick(ctx,*args):
    try:
        for i in args:
            # 指定した時間が登録されているか
            if i in guild[ctx.author.guild.id].time:
                Candidate = guild[ctx.author.guild.id].time[i].name + guild[ctx.author.guild.id].time[i].res
                Dip = random.choice(Candidate)
                if Dip[:1] == "補" or Dip[:1] == "仮":
                    Dip = Dip[1:]
                Out = ctx.guild.get_member_named(Dip)
        await ctx.send(Out.mention + "さん外交お願いします。")
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

###経験値確認
@bot.command()
async def exp(ctx,*args):
    try:
        if len(args) == 0:
            await ctx.send("```please type 「!exp team」or「!exp player」```")
        else:
            data = 0
            embed = discord.Embed()
            if args[0] == "team":
                Team = ctx.guild.name
                img = ctx.guild.icon_url
                team_id = team.range("A2:A1000")
                count = 0
                for i in team_id:
                    count += 1
                    if i.value == "":
                        if data == 0:
                            embed.set_author(name=Team+" status",icon_url=img)
                            embed.add_field(name="No Data",value="Not found",inline=True)
                        break
                    elif str(ctx.guild.id) == i.value:
                        data = 1
                        embed.set_author(name=Team+" status",icon_url=img)
                        embed.add_field(name="Lv",value=team.cell(count+1,4).value,inline=True)
                        embed.add_field(name="next Lv",value=team.cell(count+1,5).value,inline=True)
                        break
            if args[0] == "player":
                Player = ctx.author.name
                img = ctx.author.avatar_url
                user_id = personal.range("A2:A1000")
                count = 0
                for i in user_id:
                    count += 1
                    if i.value == "":
                        if data == 0:
                            embed.set_author(name=Player+"'s status",icon_url=img)
                            embed.add_field(name="No Data",value="Not found",inline=True)
                        break
                    elif str(ctx.author.id) == i.value:
                        data = 1
                        embed.set_author(name=Player+"'s status",icon_url=img)
                        embed.add_field(name="Lv",value=show.cell(count+1,3).value,inline=True)
                        embed.add_field(name="next Lv",value=show.cell(count+1,4).value,inline=True)
                        embed.add_field(name="Total EXP",value=show.cell(count+1,2).value + " exp",inline=True)
                        for j in range(0,10,2):
                            if show.cell(count+1,j+5).value == "":
                                break
                            else:
                                embed.add_field(name=show.cell(count+1,j+5).value,value=show.cell(count+1,j+6).value + " exp",inline=True)
            if args[0] == "team" or args[0] == "player":
                await ctx.send(embed=embed)
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        mes = "".join(t)
        await debug(ctx,mes)
# -------------------------------------------------------------------------------------------------------------

bot.run(token)
