<?php
namespace Sample;

class Theme extends \IastateTheme\Theme
{
    public function init()
    {
        $this->setOptions(array(
            'site_title' => 'Iowa Daily Erosion Project (IDEP)',
            'sidebar' => array(
                array(
                    'label' => 'Home',
                    'uri' => '/',
                ),
                array(
                    'label' => 'Map',
                    'uri' => '/map/',
                ),
                array(
                    'label' => 'Documentation',
                	'showchildren' => True,
                	'pages' => Array(
            			array('label' => 'Climate Files', 
            				  'uri' => 'docs/climate.phtml'),
            		),
                ),
            	array(
                    'label' => 'Diagnostics',
                	'showchildren' => True,
                	'pages' => Array(
            			array('label' => 'Compare v1 v2', 
            				  'uri' => 'compare.phtml'),
            		),
                ),
             ),
            'page_footer' => '<p>Department of Agronomy, 2101 Agronomy Hall, (515) 294-5978, '. $this->email('email') .'.</p>',
        ));
    }
}
?>
