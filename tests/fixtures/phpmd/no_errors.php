<?php
class Widget {

    public function __construct($initial)
    {
        $this->counter = $initial;
    }

    public function increment()
    {
        $this->counter += 1;
    }
}
