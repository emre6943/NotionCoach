Notion Template
https://amape.notion.site/Exercises-cd2b955dfe954be9a32ea400b445b71a

Create an Integration In Notion and add the integration to the
sesions, moves, and excersizes table
check how to do that in here https://developers.notion.com/docs/getting-started

Your .env should look like this
SECRET_TOKEN=(secret token from notion api)
SESION_TABLE=(the id of the database, you can see in the link if you fo to that table)
MOVES_TABLE=(the id of the database, you can see in the link if you fo to that table)
EXCERSIZE_TABLE=(the id of the database, you can see in the link if you fo to that table)

Test
Create a sesion and add some excersizes to it uncheck the sesion in the table,
then run the NotionApi.py, if there is no errors your sesion table should have been updated and you should see scores

Set up the cron job for Updating
I set mine up for everyday at 3:00, I would suggest setting yours once a day too and at a time you are sleeping.
start here if you have no idea https://linuxtect.com/linux-crontab-format/

Questions
For questions just comment to my video => and while you are there liking would make my day :*
