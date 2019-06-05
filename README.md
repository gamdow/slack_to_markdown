# slack-to-markdown
Utility for converting data exported from Slack to Markdown as a daily log with embedded assets.

# Example Usage
```python
>>> import slack_to_markdown as sc
>>> zip_file = "Slack export.zip"
>>> print(sc.get_user_names(zip_file))
{'alice','bob','carol',}
>>> sc.convert(zip_file, start_date=(2018,1,1), end_date=(2019,1,1), my_user_name='alice', users=['alice','bob','carol','david'], channels=['general'])
```
