from openai import OpenAI

client = OpenAI(api_key='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')



def generate_image_openAI(data: dict) -> str:
    """

    :param prompt: a string for sending to dall-e
    :param size:3 options "1024x1024" or "1024x1792" or "1792x1024"
    :param quality: 2 options. "HD" or "standard"
    :return: image_direct_url
    """

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=data[
                       'prompt'] + "I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:",
            size=data['size'],
            quality=data['quality'],
            n=1,
        )

        image_url = response.data[0].url
        print(image_url)
        return image_url
    except Exception as e:
        # Check if the error is related to content policy violation
        if 'content_policy_violation' in str(e):
            raise Exception("متنی که نوشتی مناسب نیست. یه بار دیگه تلاش کن")
        else:
            # Return a general error message for other types of errors
            raise Exception("یه مشکلی پیش اومد. دوباره امتحان کن :)")
