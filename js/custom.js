!function(e){"use strict";function n(){e(".navbar").scrollspy({offset:-76});var n=e(".large-news-image").height(),a=n-6;e(".news-two-column").css({height:a-n/2+"px"})}AOS.init(),e(".navbar-nav .nav-link").click(function(){e(".navbar-collapse").collapse("hide")}),e(window).on("resize",n),e(document).on("ready",n),e('a[href*="#"]').click(function(n){if(location.pathname.replace(/^\//,"")==this.pathname.replace(/^\//,"")&&location.hostname==this.hostname){var a=e(this.hash);(a=a.length?a:e("[name="+this.hash.slice(1)+"]")).length&&(n.preventDefault(),e("html, body").animate({scrollTop:a.offset().top-66},1e3))}})}(window.jQuery);
