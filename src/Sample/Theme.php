<?php
namespace Sample;

class Theme extends \IastateTheme\Theme
{
    public function init()
    {
        $this->setOptions(array(
            'site_title' => 'Department Title',
            'sidebar' => array(
                array(
                    'label' => 'Home',
                    'uri' => '/',
                ),
                array(
                    'label' => 'Sample',
                    'uri' => '/sample/',
                ),
            ),
            'page_footer' => '<p>Unit name, address, (555) 555-5555, '. $this->email('email') .'.</p>',
        ));
    }
}
?>
