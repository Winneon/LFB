import sys, os, re, time, argparse, getpass, praw, requests, reddit, config

current = {

	'credentials': {
	
		'username': '',
		'password': '',
		
	},
	
	'limit': '',
	'banned': [],
	
}

config_name = 'config.json'
sub_regex = re.compile(' r/[A-Za-z0-9_]+')

def bootup():
	
	version = "1.3"
	
	parse = argparse.ArgumentParser(description = 'LinkFixerBot')
	parse.add_argument('-l', '--login', action = 'store_true', help = 'Login to a different account than config account')
	args = parse.parse_args()
	
	print('\nLFB // version ' + version)
	print('------------------')
	
	if not os.path.isfile(config_name):
		
		config.write(current, config_name)
		print('> Created config.json. Please edit the values in the config before continuing.')
		sys.exit()
		
	conf = config.load(config_name)
	
	if conf['limit'] == '':
		
		print('> The limit in the config is not set! Please set it to a proper number.')
		sys.exit()
		
	elif conf['limit'] > '500':
		
		print('> The limit in the config is over 500! Please make it a lower number.')
		sys.exit()
		
	if args.login:
		
		user = raw_input('> Reddit username: ')
		passwd = getpass.getpass("> %s's password: " % user)
		
		print
		
	else:
		
		user = conf['credentials']['username']
		passwd = conf['credentials']['password']
		
		current['credentials']['username'] = user
		current['credentials']['password'] = passwd
		
		current['limit'] = conf['limit']
		
	agent = (
		'/u/' + user + ' running LinkFixerBot, version ' + version + ', created by /u/WinneonSword.'
	)
	
	banned = []
	
	r = praw.Reddit(user_agent = agent)
	reddit.login(user, passwd, r)
	
	loop(user, r, conf, banned)
	
def loop(user, reddit, conf, banned):
	
	cache = []
	
	print('\n> Booting up LFB. You will be notified when LFB detects a broken link.')
	print('> To stop the bot, press Ctrl + C.')
	
	try:
		
		while True:
			
			inbox = None
			inbox = reddit.get_unread(limit = None)
			
			print('\n> Checking mailbox for messages...')
			
			for message in inbox:
				
				try:
					
					if "+delete " in message.body:
						
						print('\n> Found potentially valid comment to be removed.')
						
						id = message.body.replace('+delete ', '')
						comment = reddit.get_info(thing_id = 't1_' + id)
						parent = reddit.get_info(thing_id = comment.parent_id)
						
						if comment.author.name == user and parent.author.name == message.author.name:
							
							print('> Comment is fully valid. Removing...')
							comment.delete()
							
							print('\n> Comment removed!')
							message.reply(
								'Congratulations! **The comment you specified, located [here](' + comment.permalink + '?context=1), has been deleted!** Thank you for using LinkFixerBot services.\n\n'
								'*****\n'
								'[^source ^code](http://github.com/WinneonSword/LFB) ^| [^subreddit](http://reddit.com/r/LinkFixerBotSnr)'
							)
							
						else:
							
							print('> Comment is not valid!')
							message.reply(
								'I am deeply sorry, but you **cannot remove the comment, located [here](' + comment.permalink + '?context=1)**! This may be because you are not the parent commenter of the comment specified in your message.\n\n'
								'*****\n'
								'[^mistake?](http://www.reddit.com/message/compose?to=WinneonSword&subject=Deletion%20Mistake&message=Replace+this+with+the+mistake+and+a+link+to+the+comment+that+needs+to+be+deleted.) ^| [^source ^code](http://github.com/WinneonSword/LFB) ^| [^subreddit](http://reddit.com/r/LinkFixerBotSnr)'
							)
							
				except:
					
					print('> Failed to remove comment.')
					
				message.mark_as_read()
				
			print('\n> Checking comments for valid entries...')
			comments = reddit.get_comments('all', limit = current['limit'])
			
			for comment in comments:
				
				cond, links = check(comment)
				subreddit = comment.subreddit.display_name
				
				if cond and subreddit.lower() not in banned and comment.id not in cache:
					
					print('\n> Valid comment found in the sub /r/%s!' % subreddit)
					
					'''if current['credentials']['username'] not in reddit.get_banned(subreddit):
						
						print("\n> The user is banned from the comment's subreddit!")
						print('> Adding subreddit to the banned subs list.')
						
						banned.append(subreddit.lower())
						
					else:
						
						cache = post(comment, links, cache)'''
						
					cache = post(reddit, comment, links, cache)
					
			print('\n> Sleeping.')
			time.sleep(15)
			
	except KeyboardInterrupt:
		
		print('> Stopped LFB. Thank you for running this bot!')
		
	except:
		
		print('\n> An error has occured. Restarting the bot.')
		loop(reddit, config, banned)
		
def check(comment):
	
	body = comment.body
	links = set(re.findall(sub_regex, body))
	cond = False
	
	if links:
		
		cond = True
		
	return cond, links
	
def post(reddit, comment, links, cache):
	
	denied_links = ''
	fixed = ''
	
	for c in links:
		
		sub = c[1:]
		text = '/' + sub + ' '
		
		if sub.lower() == 'r/' + comment.subreddit.display_name.lower():
		
			denied_links += text
		
		else:
		
			try:
				
				check = sub.replace('r/', '')
				reddit.get_subreddit(check).get_hot(limit = 1).next()
				
				fixed += text
				
			except:
				
				denied_links += text
				
	if fixed == '':
		
		print('> All broken links are the same as the sub or they are invalid links!')
		
	else:
		
		try:
			
			replied = comment.reply('This will be edited momentarily.')
			cache.append(comment.id)
			
			reply = (
				fixed + '\n\n'
				'*****\n'
				'[^report ^a ^**problem**](http://reddit.com/r/LinkFixerBotSnr) ^| [^delete ^comment](http://www.reddit.com/message/compose?to=LinkFixerBotSnr&subject=Comment%20Deletion%20%28Parent%20Commenter%20Only%29&message=%2Bdelete+' + replied.id + ') ^| [^source ^code](http://github.com/WinneonSword/LFB) ^| [^contact ^developer](http://reddit.com/user/WinneonSword)'
			)
			
			replied.edit(reply)
			print('> Comment posted! Fixed links: %s' % fixed)
			
			if not denied_links == '':
				
				print('> Denied links: %s' % denied_links)
				
		except:
			
			print('> Failed to post comment.')
			
	return cache
	
bootup()
