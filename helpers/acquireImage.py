#Download the current UT Tower photo

import requests

def acquireImage():
    url = "http://wwc.instacam.com/instacamimg/UTAUS/UTAUS_l.jpg"
    img_data = requests.get(url).content
    with open("tower.jpg","wb") as handler:
        handler.write(img_data)
        print("Image downloaded")
        path = "tower.jpg"

    return path

#acquireImage()
