class WrappermojoFrame
	constructor: (wrapper) ->
		@wrapperCmd = wrapper.cmd
		@wrapperResponse = wrapper.ws.response
		console.log "WrappermojoFrame", wrapper

	cmd: (cmd, params={}, cb=null) =>
		@wrapperCmd(cmd, params, cb)

	response: (to, result) =>
		@wrapperResponse(to, result)

	isProxyRequest: ->
		return window.location.pathname == "/"

	certSelectGotoSite: (elem) =>
		href = $(elem).attr("href")
		if @isProxyRequest() # Fix for proxy request
			$(elem).attr("href", "http://mojo#{href}")


window.mojoframe = new WrappermojoFrame(window.wrapper)
