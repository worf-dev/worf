def features_profile(profile, user, access_token):
    if user.features is not None:
        profile["user"]["features"] = user.features.features
    else:
        profile["user"]["features"] = []
