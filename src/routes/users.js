const express = require('express');
const router = express.Router();

const userController = require('../app/controllers/UserController.js');

router.post('/store', userController.store);
router.get('/create', userController.create);
router.get('/:slug', userController.show);
router.get('/', userController.index);

module.exports = router;
