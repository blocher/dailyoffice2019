from bs4 import BeautifulSoup
import requests


def get_parish_list():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    }

    f = open("congregations.txt", "w")

    for i in range(1, 1581):

        r = requests.get("http://www.acna.org/admin_units/{}".format(i), headers=headers)

        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            name = soup.find("h1").text
            diocese = soup.find("div", id="breadcrumbs").find("a").text

            if name == "The page you were looking for doesn't exist.":
                continue

            email = ""
            email_p = soup.find("p", class_="break")
            if not email_p:
                continue
            email = email_p.text

            if email == "example@example.com":
                continue

            name = name.replace('"', "").replace(",", " ").strip()
            email = email.replace('"', "").replace(",", " ").strip()
            diocese = diocese.replace('"', "").replace(",", " ").strip()

            result = '"{}","{}","{}","{}"'.format(i, name, email, diocese)
            print(result)
            f.write("{}\n".format(result))
    f.close()
