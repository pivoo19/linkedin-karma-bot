"""English translations for LinkedIn Karma Bot.

This module contains all English language strings used throughout the bot.
"""

translations = {
    # User status and karma messages
    "asks_support": "asks for support",
    "per_week": "Per week",
    "support": "Support",
    "posts": "Posts",
    "newcomer": "newcomer",
    "veteran": "veteran",
    "your_karma": "Your karma",
    "weekly": "weekly",
    "total": "total",
    "supported_all_time": "🎖️{count} - supported others all-time",
    "of_which_first_hour": "of which in first hour: {count}",

    # Leaderboard messages
    "top_weekly": "Top supporters this week",
    "top_all": "All-time top supporters",
    "no_data": "No data yet",

    # Statistics
    "stats_title": "Group Statistics",
    "total_users": "Total users",
    "total_posts": "Total posts",
    "total_reactions": "Total reactions",
    "weekly_posts": "Posts this week",
    "weekly_reactions": "Reactions this week",

    # Commands help
    "help_text": """
Hello! I'm a bot for tracking karma from LinkedIn posts.

How it works:
1. Share a link to your LinkedIn post
2. Other members react to your message
3. You earn karma for their support

Available commands:
/start - Start working with the bot
/help - Show this help message
/karma - View your karma
/top - Top members this week
/top_all - All-time top members
/stats - Group statistics

Admin commands:
/set_lang <ru|en> - Set group language
/set_period <days> - Set karma calculation period
/set_veteran <number> - Set veteran status threshold
/set_post_cost <number> - Set post cost in karma points
/reset_karma @username - Reset user's karma
/export - Export statistics to CSV

Rating system:
⭐ - 1-2 karma points
⭐⭐ - 3-5 points
⭐⭐⭐ - 6-10 points
⭐⭐⭐⭐ - 11-20 points
⭐⭐⭐⭐⭐ - 21+ points

Supported links:
- linkedin.com/posts/...
- linkedin.com/feed/update/...
- linkedin.com/pulse/...

Good luck earning karma!
""",

    # Admin messages
    "admin_only": "This command is only available to administrators",
    "setting_updated": "Setting updated",
    "invalid_value": "Invalid value",
    "language_set": "Group language set to: {value}",
    "karma_period_set": "Karma period set to: {value} days",
    "veteran_threshold_set": "Veteran threshold set to: {value} points",
    "post_cost_set": "Post cost set to: {value} points",

    # Post messages
    "post_registered": "Post registered!",
    "post_already_registered": "This post is already registered",
    "first_post": "Congratulations on your first post!",
    "not_enough_karma": "Not enough karma to post. Required: {required}, you have: {current}",
    "post_newcomer": "📝 {username} asks for support (🌱{all_time})\nFor the last {period} days:\n🙌 Supported others: {karma}\n🚀 Of which in first hour: {first_hour}\n🤝 Asked for support: {posts}",
    "post_veteran": "📝 {username} asks for support ({all_time})\nFor the last {period} days:\n🙌 Supported others: {karma}\n🚀 Of which in first hour: {first_hour}\n🤝 Asked for support: {posts}",
    "post_regular": "📝 {username} asks for support ({all_time})\nFor the last {period} days:\n🙌 Supported others: {karma}\n🚀 Of which in first hour: {first_hour}\n🤝 Asked for support: {posts}",

    # Reaction messages
    "reaction_added": "Support counted!",
    "cannot_react_own": "You cannot react to your own post",
    "already_reacted": "You already supported this post",

    # Error messages
    "error_occurred": "An error occurred. Please try again later.",
    "no_linkedin_url": "Message does not contain a LinkedIn URL",
    "user_not_found": "User not found",
    "group_only_command": "This command works only in groups. Use it in a group where the bot is active.",

    # Welcome message
    "welcome": """
Welcome to the group!

This bot helps members support each other by tracking LinkedIn posts.

To learn more, use the /help command
""",
    "commands_list": """
Available commands:
/start - Start working with the bot
/help - Show help message
/karma - View your karma
/top - Top members this week
/top_all - All-time top members
/stats - Group statistics
""",

    # Misc
    "position": "#",
    "points": "points",
    "user": "user",
    "deleted_user": "deleted user",
    
    # Admin notifications
    "admin_notification": "🔔 New help request\n\n{response}\n\n📎 Message link: {message_link}",
    "group_name_block": " \"{title}\"",
    "user_notification": "🔔 New post in group{group_name_block}\n\n{response}\n\n📎 Message link: {message_link}",
}
