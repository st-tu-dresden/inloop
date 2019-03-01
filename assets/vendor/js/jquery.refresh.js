/**
 * Refresh is a jQuery plugin which makes it easy to continuously update
 * selected elements with data polled from an arbitrary JSON endpoint.
 *
 * @author Martin Morgenstern
 * @license GNU GPL v3 - https://opensource.org/licenses/GPL-3.0
 *
 * Copyright (C) 2016 Martin Morgenstern
 */

+function($) {
  "use strict";

  /**
   * Generate a closure that polls using the given options.
   */
  function refreshClosure(options) {
    return function() {
      // ensure the success callback is executed in element context
      var success_proxy = $.proxy(options.success, this);
      var id = $(this).attr("data-id");
      $.getJSON(options.url.replace(":id:", id), success_proxy);
    }
  }

  /**
   * Initialize / uninitialize refreshing for a specific element.
   */
  var actions = {
    activate: function(options) {
      var refresh_proxy = $.proxy(refreshClosure(options), this);
      refresh_proxy();
      this._refreshInterval = window.setInterval(refresh_proxy, options.interval);
    },
    deactivate: function() {
      if (this._refreshInterval) {
        window.clearInterval(this._refreshInterval);
        this._refreshInterval = null;
      }
    }
  }

  /**
   * Enable or disable refreshing on a selection of elements.
   */
  $.fn.refreshJSON = function(action, options) {
    var fn = action ? actions[action] : actions.activate;
    if (!fn) {
      throw new Error("Unknown action: " + action);
    }
    // init or uninit each element separately
    this.each(function() {
      fn.call(this, options);
    });
    return this;
  }
}(jQuery);
