<?php

declare(strict_types=1);

require_once __DIR__ . '/../../../../config/database.php';

class BaseModel
{
    protected $conn;

    public function __construct()
    {
        global $conn;
        $this->conn = $conn;
    }
}
