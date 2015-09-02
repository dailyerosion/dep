<?php 
require '../config/settings.inc.php';
require_once '../include/myview.php';

$t = new MyView();

$t->title = 'Project Disclaimer';

$t->content = <<<EOF
<h3>DEP Disclaimer</h3>

<p>This website provides <strong>modelled</strong> estimates of sheet and rill
	soil erosion.  The values presented are not observations.  This information
	is provided for educational and research usage only.</p>

EOF;

$t->render('single.phtml');
?>