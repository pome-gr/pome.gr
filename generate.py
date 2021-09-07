import io
import os
import shutil
import frontmatter
import re
import markdown
import json
from jinja2 import FileSystemLoader, Environment
from os import listdir
from datetime import datetime


menu = [("https://dna.hamilton.ie", "Home"),
        ("/people.html", "People"),
        ("/publications.html", "Publications"),
        ("/software.html", "Software"),
        ("/join.html", "Join us"),
        ("https://www.maynoothuniversity.ie/hamilton", "Hamilton Institute")]


ignore_files = [".DS_Store", ".gitignore",
                "requirements.txt", "README.md", "post-commit", "main.css", "trigger_remote_build.sh"]


posts = []

date_re = re.compile(r'^(\d+)-(\d+)-(\d+)-.*')
for f in reversed(sorted(listdir("posts"))):
    pre, ext = os.path.splitext(f)
    if ext == ".html" or ext == ".md":
        post = frontmatter.load("posts/"+f)
        def p(): return None
        p.title = post["title"]
        p.headline = post.get("headline", "")
        m = date_re.match(f)
        year = m.group(1)
        month = m.group(2)
        day = m.group(3)
        date = datetime(int(year), int(month), int(day), 0, 0)
        p.date = datetime.strftime(date, '%b %d, %Y')
        url = pre + ".html"
        p.url = post.get("url", url)
        posts.append((p, (f, post, date)))

if 'WEBSITE_MODE' in os.environ and os.environ['WEBSITE_MODE'] == 'prod':
    PROD = True
    DESTINATION = "/var/www/html/"
else:
    PROD = False
    DESTINATION = "_site/"

print("opening templates/page.html")
with io.open("templates/page.html", mode="r", encoding="utf-8") as templ:
    page_template = templ.read().strip()
page_template = Environment(loader=FileSystemLoader(
    "templates")).from_string(page_template)

for f in listdir("."):
    pre, ext = os.path.splitext(f)

    if os.path.isfile(f) and f not in ignore_files:
        print("opening "+f)
        with io.open(f, mode="r", encoding="utf-8") as templ:
            data = templ.read().strip()
        print("opened "+f)

    template = Environment(loader=FileSystemLoader(
        "templates")).from_string(data)

    if ext == ".html":
        rendered = template.render(
            menu=menu,
            posts=posts,
        )
        with open(DESTINATION + pre + ".html", "w") as out:
            out.write(rendered)

    elif ext == ".md":
        rendered = template.render(
            posts=posts,
            contents=markdown.markdown(data),
        )  # <- this is not used but allows to use templating in root .md
        rendered = page_template.render(
            menu=menu,
            posts=posts,
            contents=markdown.markdown(rendered),
        )
        with open(DESTINATION + pre + ".html", "w") as out:
            out.write(rendered)

    elif ext == ".css":
        src = f
        dest = DESTINATION+f
        # copy only if changes were done (ie update times differ by 1sec)
        if not os.path.exists(dest) or os.stat(src).st_mtime - os.stat(dest).st_mtime > 1:
            shutil.copy2(src, dest)


with io.open("templates/post.html", mode="r", encoding="utf-8") as templ:
    post_template = templ.read().strip()
post_template = Environment(loader=FileSystemLoader(
    "templates")).from_string(post_template)

for (_, (f, p, date)) in posts:
    pre, ext = os.path.splitext(f)
    if ext == ".md" or ext == ".html":
        template = Environment(loader=FileSystemLoader(
            "templates")).from_string(p.content)

        rendered = template.render(
            posts=posts,
            title=p.get("title", ""),
            author=p.get("author", ""),
            date=datetime.strftime(date, '%b %d, %Y'),
            dateTime=datetime.strftime(date, '%Z'),
        )
        rendered = post_template.render(
            menu=menu,
            posts=posts,
            title=p.get("title", ""),
            author=p.get("author", ""),
            date=datetime.strftime(date, '%b %d, %Y'),
            dateTime=datetime.strftime(date, '%Z'),
            content=markdown.markdown(rendered)
        )
        with open(DESTINATION + pre + ".html", "w") as out:
            out.write(rendered)

os.system("rsync -a assets/ _site/assets")
print(f"Website successfully generated")
