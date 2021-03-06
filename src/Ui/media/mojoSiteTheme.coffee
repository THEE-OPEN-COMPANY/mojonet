DARK = "(prefers-color-scheme: dark)"
LIGHT = "(prefers-color-scheme: light)"

mqDark = window.matchMedia(DARK)
mqLight = window.matchMedia(LIGHT)


changeColorScheme = (theme) ->
    mojoframe.cmd "userGetGlobalSettings", [], (user_settings) ->
        if user_settings.theme != theme
            user_settings.theme = theme
            mojoframe.cmd "userSetGlobalSettings", [user_settings], (status) ->
                if status == "ok"
                    location.reload()
                return
        return
    return


displayNotification = ({matches, media}) ->
    if !matches
        return

    mojoframe.cmd "siteInfo", [], (site_info) ->
        if "ADMIN" in site_info.settings.permissions
            mojoframe.cmd "wrapperNotification", ["info", "Your system's theme has been changed.<br>Please reload site to use it."]
        else
            mojoframe.cmd "wrapperNotification", ["info", "Your system's theme has been changed.<br>Please open mojoHello to use it."]
        return
    return


detectColorScheme = ->
    if mqDark.matches
        changeColorScheme("dark")
    else if mqLight.matches
        changeColorScheme("light")

    mqDark.addListener(displayNotification)
    mqLight.addListener(displayNotification)

    return


mojoframe.cmd "userGetGlobalSettings", [], (user_settings) ->
    if user_settings.use_system_theme == true
        detectColorScheme()

    return
