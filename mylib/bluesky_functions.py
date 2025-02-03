from atproto import Client, models


def post_message_bluesky(
    username, password, title, message, img_data, url, price, tags
):
    # Ensure the message does not exceed 300 graphemes
    message = message[:297] + "..."  # Truncate message to 300 characters

    client = Client()
    client.login(username, password)

    thumb = client.upload_blob(img_data)
    embed = models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            title=title,
            description=message,
            uri=url,
            thumb=thumb.blob,
        )
    )
    # Format tags as hashtags
    hashtags = " ".join([f"#{tag}" for tag in tags])

    post = client.send_post(
        f"{title} با تخفیف قیمت {price} دلار {hashtags}",
        embed=embed,
        langs=["fa", "fa-IR"],
    )
    return post.cid
