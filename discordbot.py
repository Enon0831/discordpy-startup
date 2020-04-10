import discord
import os
import pickle
import member

client = discord.Client()
token = os.environ['DISCORD_BOT_TOKEN']
guild = {}

f_name = "./tmp/guild.pickle"

#プログラム再起動時のインスタンス読み込み
try:
    f = open(f_name,'rb')
    guild = pickle.load(f)
    f.close
except EOFError:
    pass
except FileNotFoundError:
    pass


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    kyosyu = 0
    mes = message.content.split()
    #他人の操作をしようとしたとき
    if (len(mes) > 1) and (mes[1][:2] == "<@"):
        id = int(mes[1][3:21])
        player = message.author.guild.get_member(id)

    # 送り主がBotだった場合反応したくないので
    if client.user != message.author:
        #サーバー登録情報が無ければ自動登録
        if not message.author.guild.id in guild:
            guild[message.author.guild.id] = member.guild()
            

        # !help でヘルプ表示
        if message.content.startswith("!help"):
            await message.channel.send(member.help())

        else:
            if message.author.guild.id in guild:
                #mention設定
                if message.content.startswith("!mention"):
                    await message.channel.send(guild[message.author.guild.id].mentionset())
                
                #交流戦時間の追加
                if message.content.startswith("!set"):
                    m = ""
                    for i in mes:
                        if  str.isdecimal(i): 
                            guild[message.author.guild.id].set(str(i))
                            if discord.utils.get(message.guild.roles, name=str(i)) == None:
                                await message.guild.create_role(name=str(i),mentionable = True)
                            m = "```\n指定した交流戦の時間を追加登録しました\n```"
                    if m == "":
                        m = "```\n追加したい交流戦の時間を数値で入力してください\n```"
                    await message.channel.send(m)

                #交流戦時間の削除
                if message.content.startswith("!out"):
                    for i in mes:
                        if i in guild[message.author.guild.id].time: 
                            guild[message.author.guild.id].out(str(i))
                            role = discord.utils.get(message.guild.roles, name=str(i))
                            await role.delete()
                            m = "```\n指定した交流戦の時間を削除しました\n```"
                    if m == "":
                        m = "```\n該当する交流戦の時間がありませんでした\n```"
                    await message.channel.send(m)

                # !clear で始まる場合は挙手リセット
                if message.content.startswith("!clear"):
                    for i in guild[message.author.guild.id].time.keys():
                        guild[message.author.guild.id].clear(str(i))
                        #役職リセット
                        role = discord.utils.get(message.guild.roles, name=str(i))
                        await role.delete()
                        await message.guild.create_role(name=str(i),mentionable = True)
                    m = member.nowhands(guild[message.author.guild.id])
                    await message.channel.send(m)
                    

                # 「!c」で始まるか調べる
                elif message.content.startswith("!c"):
                    kyosyu = 1
                    #他人の追加
                    if (mes[1][:2] == "<@"):
                        m = player.name + "さんの挙手を追加します"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                if not player.name in guild[message.author.guild.id].time[i].name:
                                    if "仮" + player.name in guild[message.author.guild.id].time[i].res:
                                        guild[message.author.guild.id].time[i].reservedel(player.name)
                                    guild[message.author.guild.id].time[i].add(player.name)
                                    role = discord.utils.get(message.guild.roles, name=str(i))
                                    await player.add_roles(role)

                    #自分の追加
                    else:
                        m = message.author.name + "さんの挙手を確認しました"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                if not message.author.name in guild[message.author.guild.id].time[i].name:
                                    if "仮" + message.author.name in guild[message.author.guild.id].time[i].res:
                                        guild[message.author.guild.id].time[i].reservedel(message.author.name)
                                    guild[message.author.guild.id].time[i].add(message.author.name)
                                    role = discord.utils.get(message.guild.roles, name=str(i))
                                    await message.author.add_roles(role)

                    
                # !rc で始まる場合は挙手
                if message.content.startswith("!rc"):
                    kyosyu = 1
                    #他人の追加
                    if (mes[1][:2] == "<@"):
                        m = player.name + "さんの仮挙手を追加します"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                if not "仮" + player.name in guild[message.author.guild.id].time[i].res:
                                    if player.name in guild[message.author.guild.id].time[i].name:
                                        guild[message.author.guild.id].time[i].sub(player.name)
                                    guild[message.author.guild.id].time[i].reserve(player.name)
                                    role = discord.utils.get(message.guild.roles, name=str(i))
                                    await player.add_roles(role)

                    #自分の追加
                    else:
                        m = message.author.name + "さんの仮挙手を確認しました"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                if not "仮" + message.author.name in guild[message.author.guild.id].time[i].res:
                                    if message.author.name in guild[message.author.guild.id].time[i].name:
                                        guild[message.author.guild.id].time[i].sub(message.author.name)
                                    guild[message.author.guild.id].time[i].reserve(message.author.name)
                                    role = discord.utils.get(message.guild.roles, name=str(i))
                                    await message.author.add_roles(role)

                # !d で始まる場合は取り下げ
                if message.content.startswith("!d"):
                    kyosyu = 1
                    if (mes[1][:2] == "<@"):
                        m = player.name + "さんの挙手を取り下げます"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                guild[message.author.guild.id].time[i].sub(player.name)
                                role = discord.utils.get(message.guild.roles, name=str(i))
                                await player.remove_roles(role)

                    #自分の追加
                    else:
                        m = message.author.name + "さんの挙手取り下げを確認しました"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                guild[message.author.guild.id].time[i].sub(message.author.name)
                                role = discord.utils.get(message.guild.roles, name=str(i))
                                await message.author.remove_roles(role)

                # !rd で始まる場合は取り下げ
                if message.content.startswith("!rd"):
                    kyosyu = 1
                    if (mes[1][:2] == "<@"):
                        m = player.name + "さんの仮挙手を取り下げます"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                guild[message.author.guild.id].time[i].reservedel(player.name)
                                role = discord.utils.get(message.guild.roles, name=str(i))
                                await player.remove_roles(role)

                    #自分の追加
                    else:
                        m = message.author.name + "さんの仮挙手取り下げを確認しました"
                        await message.channel.send(m)
                        for i in mes:
                            if i in guild[message.author.guild.id].time:
                                guild[message.author.guild.id].time[i].reservedel(message.author.name)
                                role = discord.utils.get(message.guild.roles, name=str(i))
                                await message.author.remove_roles(role)

                #現在挙手状況の確認
                if message.content.startswith("!now"):
                    await message.channel.send(member.nowhands(guild[message.author.guild.id]))
                    
                
                # 挙手状態が変更されるとき
                if kyosyu == 1:
                    # メッセージ内容の変更
                    await message.channel.send(member.nowhands(guild[message.author.guild.id]))
                    

                    
        #インスタンス保存準備
        f = open(f_name,'wb')     
        pickle.dump(guild,f)
        #インスタンス保存
        f.close
        

client.run(token)
