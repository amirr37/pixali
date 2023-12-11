from openai import OpenAI

client = OpenAI(api_key='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')


# response = client.images.generate(
#     model="dall-e-3",
#     prompt="a strong bodybuilder man holing dumble .",
#     size="1024x1024",
#     quality="standard",
#     n=1,
# )
#
# image_url = response.data[0].url
#
# print(image_url)


def generate_image_openAI(data: dict) -> str:
    """

    :param prompt: a string for sending to dall-e
    :param size:3 options "1024x1024" or "1024x1792" or "1792x1024"
    :param quality: 2 options. "HD" or "standard"
    :return: image_direct_url
    """

    response = client.images.generate(
        model="dall-e-3",
        prompt=data['prompt'],
        size=data['size'],
        quality=data['quality'],
        n=1,
    )

    image_url = response.data[0].url
    print(image_url)
    return image_url
