<?php 
require '../config/settings.inc.php';
require_once '../include/myview.php';

$t = new MyView();

$t->title = 'Project Contacts';

$t->content = <<<EOF
<h3>Project Contacts</h3>

<p><b>Principal Investigator:</b> Dr Rick Cruse  
<br /><i>Email:</i>  <a href="mailto:rmc@iastate.edu">rmc@iastate.edu</a></p>

<p><b>Technical/Webmaster:</b> Daryl Herzmann
<br /><i>Email:</i> <a href="mailto:akrherz@iastate.edu">akrherz@iastate.edu</a></p>

EOF;

$t->render('single.phtml');
?>