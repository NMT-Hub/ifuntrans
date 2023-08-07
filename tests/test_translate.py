import ifuntrans.api.translate as translate


def test_translate():
    data = {"engine": "google", "sourceLan": "auto", "targetLan": "en", "translateSource": "Bonjour le monde"}
    request = translate.TranslationRequest(**data)
    response: translate.TranslationResponse = translate.translate(request) 
    assert isinstance(response, translate.TranslationResponse)
