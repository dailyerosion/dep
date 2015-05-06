<?php 
require '../config/settings.inc.php';
require_once '../include/myview.php';

$t = new MyView();

$t->title = 'Project Contacts';

$t->content = <<<EOF
<h3>Project Contacts...</h3>
EOF;

$t->render('single.phtml');
?>