var currentTab = null;
function handleClick(target){	
	for (i=1;i<5;i++){
		$('#q'+i).hide();
	}
	$('#q'+target).show();
	// 1. If no currentTab, show the offcanvas
	if ( currentTab == null){		
		$('.row-offcanvas').toggleClass("active");
		currentTab = target;
	}
	// 2. current tab was clicked again
	else if (currentTab == target ){
		$('.row-offcanvas').toggleClass("active");
		currentTab = null;
	} else {
		currentTab = target;
	}
}

$(document).ready(function () {
	  $('[data-target="q1"]').click(function (event) {
		    handleClick(1);
		  });
	  $('[data-target="q2"]').click(function (event) {
		    handleClick(2);
		  });
	  $('[data-target="q3"]').click(function (event) {
		    handleClick(3);
		  });
	  $('[data-target="q4"]').click(function (event) {
		    handleClick(4);
		  });
	  $("#close_sidebar").click(function(){
		 handleClick(currentTab); 
	  });
});
