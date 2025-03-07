import discord
from discord.ext import commands
import datetime
import asyncio
from collections import defaultdict
import random

TOKEN = 'MTM0MDUwNjkxMjc3MjQ2MDU2NQ.G8xKDJ.VKLMOVuBA_fayhSZsezG1vBpQyOS5rDJma_dhU'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix='.', intents=intents)

message_counts = defaultdict(lambda: defaultdict(int))
SPAM_THRESHOLD = 5
SPAM_TIME_WINDOW = 5

JOIN_THRESHOLD = 10
JOIN_TIME_WINDOW = 10
recent_joins = []

WIN_THRESHOLD = 3
WIN_TIME_WINDOW = 3600  

user_slot_wins = defaultdict(list)

@client.event
async def on_ready():
    print(f"Bot is ready as {client.user}")
    await client.change_presence(activity=discord.Game(name=".help for commands"))
    client.add_view(TicketView())
    client.add_view(CloseTicketView())

@client.event
async def on_member_join(member):
    recent_joins.append(datetime.datetime.now())
    while recent_joins and (datetime.datetime.now() - recent_joins[0]).seconds > JOIN_TIME_WINDOW:
        recent_joins.pop(0)
    
    if len(recent_joins) >= JOIN_THRESHOLD:
        await member.guild.edit(verification_level=discord.VerificationLevel.high)
        channel = discord.utils.get(member.guild.channels, name='mod-logs')
        if channel:
            await channel.send(f"Possible raid detected! Verification level increased.")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    current_time = datetime.datetime.now()
    message_counts[user_id][current_time] += 1

    for time in list(message_counts[user_id].keys()):
        if (current_time - time).seconds > SPAM_TIME_WINDOW:
            del message_counts[user_id][time]

    if sum(message_counts[user_id].values()) >= SPAM_THRESHOLD:
        await message.author.timeout(datetime.timedelta(minutes=5))
        await message.channel.send(f"{message.author.mention} has been muted for spamming.")
        message_counts[user_id].clear()

    await client.process_commands(message)

@client.command()
async def clear(ctx, amount: int):
    if ctx.author.guild_permissions.manage_messages:
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f'Cleared {amount} messages!')
        await asyncio.sleep(3)
        await msg.delete()

@client.command()
async def sendmessage(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

@client.command()
@commands.cooldown(1, 300, commands.BucketType.user)
async def slotroll(ctx):
    global user_slot_wins
    current_time = datetime.datetime.now()
    
    user_wins = user_slot_wins[ctx.author.id]
    user_wins = [t for t in user_wins if (current_time - t).seconds < WIN_TIME_WINDOW]
    user_slot_wins[ctx.author.id] = user_wins
    
    if len(user_wins) >= WIN_THRESHOLD:
        await ctx.send(f"{ctx.author.mention} you have reached your win limit. Please try again later.")
        return

    emojis = ["🎮", "🎲", "💎", "🎯", "🎪", "🎨", "🎭"]
    weights = [0.35, 0.35, 0.0001, 0.1, 0.0666, 0.0666, 0.0667]
    slots = [random.choices(emojis, weights=weights)[0] for _ in range(3)]
    
    slot_message = await ctx.send(f"Spinning... [{slots[0]} | {slots[1]} | {slots[2]}]")
    
    for _ in range(7):
        await asyncio.sleep(0.5)
        slots = [random.choices(emojis, weights=weights)[0] for _ in range(3)]
        await slot_message.edit(content=f"Spinning... [{slots[0]} | {slots[1]} | {slots[2]}]")
    
    if slots[0] == slots[1] == slots[2]:
        user_slot_wins[ctx.author.id].append(current_time)
        
        if slots[0] == "💎":
            win_embed = discord.Embed(
                title="🎉 JACKPOT! GRAND PRIZE! 🎉",
                description="You've won a Steam account\nPlease DM Jupiter with a screenshot of this message as proof.",
                color=discord.Color.gold()
            )
            win_embed.add_field(name="Prize Details", value="• 5 GTAG STEAM ACCOUNTS\n• Special Winner Role", inline=False)
            win_embed.set_footer(text="Congratulations on hitting the jackpot!")
            await ctx.author.send(embed=win_embed)
            await slot_message.edit(content=f"🎊 JACKPOT! 🎊 [{slots[0]} | {slots[1]} | {slots[2]}]")
        else:
            win_embed = discord.Embed(
                title="🎉 Small Win! 🎉",
                description="You've won a Steam account\nPlease DM Jupiter with a screenshot of this message as proof.",
                color=discord.Color.green()
            )
            win_embed.add_field(name="Prize Details", value="• 1 Gtag Steam Account", inline=False)
            await ctx.author.send(embed=win_embed)
            await slot_message.edit(content=f"Winner! [{slots[0]} | {slots[1]} | {slots[2]}]")
    else:
        lose_embed = discord.Embed(
            title="Almost there!",
            description="You didn't win this time. Better luck next time",
            color=discord.Color.red()
        )
        await slot_message.edit(content=f"Better luck next time [{slots[0]} | {slots[1]} | {slots[2]}]", embed=lose_embed)

@client.command()
async def giveaway(ctx, time: str, *, prize: str):
    await ctx.message.delete()
    
    unit = time[-1].lower()
    value = int(time[:-1])
    
    if unit == 's':
        seconds = value
    elif unit == 'm':
        seconds = value * 60
    elif unit == 'h':
        seconds = value * 60 * 60
    elif unit == 'd':
        seconds = value * 60 * 60 * 24
    elif unit == 'w':
        seconds = value * 60 * 60 * 24 * 7
    else:
        await ctx.send("Invalid time format! Use s/m/h/d/w")
        return    
    end_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)
    embed = discord.Embed(
         title="🎉 Giveaway Alert! 🎉",
         description=(
             f"Prize: **{prize}**\n\n"
             f"React with 🎉 to enter!\n"
             f"The giveaway ends at <t:{int(end_time.timestamp())}:F> (<t:{int(end_time.timestamp())}:R>)."
         ),
         color=discord.Color.gold(),
         timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.set_footer(text=f"Hosted by {ctx.author.display_name}")
    
    giveaway_message = await ctx.send("@everyone", embed=embed)
    await giveaway_message.add_reaction("🎉")
    
    await asyncio.sleep(seconds)
    
    try:
         finished_message = await ctx.channel.fetch_message(giveaway_message.id)
    except discord.NotFound:
         return

    reaction = discord.utils.get(finished_message.reactions, emoji="🎉")
    if reaction:
         users = await reaction.users().flatten()
         participants = [user for user in users if not user.bot]
         if len(participants) == 0:
             result_text = "No valid participants entered the giveaway."
         else:
             winner = random.choice(participants)
             result_text = f"Congratulations {winner.mention}! You have won **{prize}**!"
         
         result_embed = discord.Embed(
             title="🎊 Giveaway Ended! 🎊",
             description=result_text,
             color=discord.Color.green(),
             timestamp=datetime.datetime.now(datetime.UTC)
         )
         result_embed.set_footer(text="Thanks for participating!")
         await ctx.send("@everyone", embed=result_embed)
    else:
         await ctx.send("Giveaway reaction not found.")

@client.command()
async def trade(ctx, user: discord.Member, *, item: str):
    try:
        await ctx.message.delete()
        
        request_embed = discord.Embed(
            title="Trade Request",
            description=f"{ctx.author} wants to trade: {item}",
            color=discord.Color.blue()
        )
        request_embed.add_field(name="Reply with", value="Type 'yes' to accept the trade", inline=False)
        
        await user.send(embed=request_embed)
        
        confirmation_embed = discord.Embed(
            title="Trade Request Sent",
            description=f"Your trade request has been sent to {user.name}",
            color=discord.Color.green()
        )
        await ctx.author.send(embed=confirmation_embed)
        
        def check(message):
            return message.author == user and isinstance(message.channel, discord.DMChannel) and message.content.lower() == 'yes'
            
        try:
            await client.wait_for('message', timeout=60.0, check=check)
            
            accepted_embed = discord.Embed(
                title="Trade Accepted",
                description=f"The trade has been accepted! A private channel has been created.",
                color=discord.Color.green()
            )
            await user.send(embed=accepted_embed)
            await ctx.author.send(embed=accepted_embed)
            
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True),
                user: discord.PermissionOverwrite(read_messages=True)
            }
            
            trades_category = discord.utils.get(ctx.guild.categories, name='trades')
            
            channel = await ctx.guild.create_text_channel(
                f'trade-{ctx.author.name}-{user.name}',
                overwrites=overwrites,
                category=trades_category
            )
            
            await channel.send(f"Trade channel created for {ctx.author.mention} and {user.mention}!")
            
        except asyncio.TimeoutError:
            await ctx.send(f"{user.mention} did not accept the trade in time.")
            
    except discord.Forbidden:
        await ctx.send("I couldn't send a DM to that user. They might have DMs disabled.")

@client.command()
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    if not ctx.author.guild_permissions.manage_channels:
        return await ctx.send("You don't have permission to lock channels.", delete_after=10)
    
    role = ctx.guild.get_role(1340483741092675587)
    overwrite = channel.overwrites_for(role)
    overwrite.send_messages = False
    overwrite.view_channel = False
    overwrite.add_reactions = False
    overwrite.create_instant_invite = False
    overwrite.attach_files = False
    overwrite.embed_links = False
    await channel.set_permissions(role, overwrite=overwrite)
    
    embed = discord.Embed(title="Channel Locked", description=f"🔒 {channel.mention} has been locked.", color=discord.Color.red())
    await ctx.send(embed=embed)

@client.command()
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    if not ctx.author.guild_permissions.manage_channels:
        return await ctx.send("You don't have permission to unlock channels.", delete_after=10)
    
    role = ctx.guild.get_role(1340483741092675587)
    overwrite = channel.overwrites_for(role)
    overwrite.send_messages = True
    overwrite.view_channel = True
    overwrite.add_reactions = True
    overwrite.create_instant_invite = True
    overwrite.attach_files = True
    overwrite.embed_links = True
    await channel.set_permissions(role, overwrite=overwrite)
    
    embed = discord.Embed(title="Channel Unlocked", description=f"🔓 {channel.mention} has been unlocked.", color=discord.Color.green())
    await ctx.send(embed=embed)

@client.command()
async def tokens(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="Discord Tokens",
        description="All items are 100% safe and secure. We do not store any of your information.",
        color=discord.Color.dark_purple()
    )
    
    embed.add_field(
        name="Discord Products",
        value="**Token Items**\n" +
              "Discord Token: `$0.08` (987 in stock)\n",
        inline=False
    )
    
    total_items = 987
    total_value = (987 * 0.08)
    
    embed.add_field(
        name="Market Statistics",
        value=f"Total Items: `{total_items}`\n" +
              f"Total Value: `${total_value:,.2f}`\n" +
              f"Last Restock: <t:{int(datetime.datetime.now().timestamp())}:R>",
        inline=False
    )
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1341105869626015744/1341135549351858216/Screenshot_2025-02-15_190718.png?ex=67b4e550&is=67b393d0&hm=36373c9e08baec91fad9755e9df9f023ce780f46cd9b4a70e03e457db6797b77&")
    embed.set_footer(text=f"Market data updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await ctx.send("@everyone", embed=embed)

@client.command()
async def nitrotokens(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="Discord Nitro Tokens",
        description="All items are 100% safe and secure. We do not store any of your information.",
        color=discord.Color.dark_purple()
    )
    
    embed.add_field(
      name="Discord Products",
      value="**Nitro Token Items**\n" +
            "Discord Nitro Basic Token: `$2.50` (543 in stock)\n" +
            "Discord Nitro Classic Token: `$3.50` (444 in stock)\n" +
            "Discord Nitro + 2 Server Boosts Token: `$5.00` (321 in stock)\n",
      inline=False
    )
    
    total_items = 543 + 444
    total_value = (543 * 2.50) + (444 * 3.50)
    
    embed.add_field(
        name="Market Statistics",
        value=f"Total Items: `{total_items}`\n" +
              f"Total Value: `${total_value:,.2f}`\n" +
              f"Last Restock: <t:{int(datetime.datetime.now().timestamp())}:R>",
        inline=False
    )
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1341105869626015744/1341135549351858216/Screenshot_2025-02-15_190718.png?ex=67b4e550&is=67b393d0&hm=36373c9e08baec91fad9755e9df9f023ce780f46cd9b4a70e03e457db6797b77&")
    embed.set_footer(text=f"Market data updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await ctx.send("@everyone", embed=embed)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="persistent_ticket_create")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")
        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}-{random.randint(1000,9999)}",
            category=category,
            topic=str(interaction.user.id)
        )
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.send(
            f"{interaction.user.mention} your ticket has been created.\n<@785339272173060096> <@1301581074475778111>",
            view=CloseTicketView()
        )
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="persistent_ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_owner_id = interaction.channel.topic
        if str(interaction.user.id) != ticket_owner_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Only the ticket owner or a moderator can close this ticket.",
                ephemeral=True
            )
            return
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await interaction.channel.delete()

    @discord.ui.button(label="Close with Reason", style=discord.ButtonStyle.danger, custom_id="persistent_ticket_close_reason")
    async def close_ticket_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_owner_id = interaction.channel.topic
        if str(interaction.user.id) != ticket_owner_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Only the ticket owner or a moderator can close this ticket.",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(TicketCloseReasonModal())


class TicketCloseReasonModal(discord.ui.Modal, title="Close Ticket with Reason"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_owner_id = interaction.channel.topic
        if str(interaction.user.id) != ticket_owner_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Only the ticket owner or a moderator can close this ticket.",
                ephemeral=True
            )
            return
        await interaction.response.send_message(f"Closing ticket. Reason: {self.reason.value}", ephemeral=True)
        await interaction.channel.delete()

@client.command()
async def tickets(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="Tickets",
        description="Click the button below to open a ticket.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())
    
@client.command()
async def membercount(ctx):
    await ctx.message.delete()
    overwrites = {}
    for role in ctx.guild.roles:
        overwrites[role] = discord.PermissionOverwrite(view_channel=True, connect=False)
    
    channel = await ctx.guild.create_voice_channel(
        f"Member Count: {ctx.guild.member_count}",
        overwrites=overwrites
    )

    @client.event
    async def on_member_join(member):
        if member.guild == ctx.guild:
            await channel.edit(name=f"Member Count: {ctx.guild.member_count}")

    @client.event
    async def on_member_remove(member):
        if member.guild == ctx.guild:
            await channel.edit(name=f"Member Count: {ctx.guild.member_count}")

@client.command()
async def nitro(ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="Discord Nitro",
            description="All items are 100% safe and secure. We do not store any of your information.",
            color=discord.Color.dark_purple()
        )
    
        embed.add_field(
            name="Discord Products",
            value="**Nitro Items**\n" +
                  "Discord Nitro Basic (Monthly): `$3.00/M` (142 in stock)\n" +
                  "Discord Nitro Classic (Monthly): `$4.00/M` (234 in stock)\n",
            inline=False
        )
    
        total_items = 142 + 234
        total_value = (142 * 3.00) + (234 * 4.00)   

        embed.add_field(
            name="Market Statistics",
            value=f"Total Items: `{total_items}`\n" +
                  f"Total Value: `${total_value:,.2f}`\n" +
                  f"Last Restock: <t:{int(datetime.datetime.now().timestamp())}:R>",
            inline=False
        )
    
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1341105869626015744/1341135549351858216/Screenshot_2025-02-15_190718.png?ex=67b4e550&is=67b393d0&hm=36373c9e08baec91fad9755e9df9f023ce780f46cd9b4a70e03e457db6797b77&")
        embed.set_footer(text=f"Market data updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
        await ctx.send("@everyone", embed=embed)

@client.command()
async def dm(ctx, user: discord.Member, *, message: str):
    await ctx.message.delete()
    try:
        await user.send(message)
        await ctx.send(f"Sent DM to {user.mention}.", delete_after=10)
    except discord.Forbidden:
        await ctx.send(f"Unable to send DM to {user.mention}.", delete_after=10)

@client.command()
async def roblox(ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="Roblox Products",
            description="All items are 100% safe and secure. We do not store any of your information.",
            color=discord.Color.dark_purple()
        )
    
        embed.add_field(
            name="Roblox Accounts with Robux",
            value="**Robux Accounts**\n" +
                  "10,000 Robux Account: `$80.00` (234 in stock)\n" +
                  "50,000 Robux Account: `$423.00` (54 in stock)\n" +
                  "100,000 Robux Account: `$864.00` (24 in stock)\n",
            inline=False
        )

        embed.add_field(
            name="Rare Item Accounts",
            value="**Items**\n" +
                  "Korblox Account: `$160.00` (123 in stock)\n" +
                  "Headless Horseman Account: `$320.00` (67 in stock)\n",
            inline=False
        )

        embed.add_field(
            name="Special Accounts",
            value="**Items**\n" +
                  "2010 Account: `$10.00` (89 in stock)\n" +
                  "2007 Account: `$20.00` (78 in stock)\n" +
                  "Builder's Club Account: `$39.00` (178 in stock)\n",
            inline=False
        )
    
        total_items = 234 + 54 + 24 + 123 + 67 + 89 + 78 + 178
        total_value = (234 * 80.00) + (54 * 423.00) + (24 * 864.00) + (123 * 160.00) + (67 * 320.00) + (89 * 10.00) + (78 * 20.00) + (178 * 39.00)
         
        embed.add_field(
            name="Market Statistics",
            value=f"Total Items: `{total_items}`\n" +
                  f"Total Value: `${total_value:,.2f}`\n" +
                  f"Last Restock: <t:{int(datetime.datetime.now().timestamp())}:R>",
            inline=False
        )
    
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1341105869626015744/1341135549351858216/Screenshot_2025-02-15_190718.png?ex=67b4e550&is=67b393d0&hm=36373c9e08baec91fad9755e9df9f023ce780f46cd9b4a70e03e457db6797b77&")
        embed.set_footer(text=f"Market data updated • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
        await ctx.send("@everyone", embed=embed)
@client.command()
async def reactionstuff(ctx):
    existing_category = discord.utils.get(ctx.guild.categories, name="Reaction Stuff")
    if existing_category:
        await ctx.send("Reaction stuff has already been set up.")
        return

    category = await ctx.guild.create_category("Reaction Stuff")

    announcement_channel = await ctx.guild.create_text_channel("Annoucement Pings", category=category)
    await announcement_channel.send("react to get Annoucement Pings")

    await ctx.send("Reaction stuff setup completed!")


@client.event
async def on_member_join(member):
    channel = client.get_channel(1340483741394665566)
    if channel is None:
        return
    embed = discord.Embed(
        title="👋 Welcome!",
        description=f"Welcome {member.mention} to the server!",
        color=discord.Color.green()
    )
    await channel.send(embed=embed)
    if member.guild == member.guild:
        await channel.edit(name=f"Member Count: {member.guild.member_count}")

@client.event
async def on_member_remove(member):
    channel = client.get_channel(1340483741394665566)
    if channel is None:
        return
    embed = discord.Embed(
        title="👋 Goodbye!",
        description=f"{member.mention} has left the server!",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)   
    if member.guild == member.guild:
        await channel.edit(name=f"Member Count: {member.guild.member_count}")

client.run(TOKEN)
