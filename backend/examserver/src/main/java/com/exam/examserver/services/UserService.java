package com.exam.examserver.services;

import java.util.Set;

import com.exam.examserver.models.UserRole;
import com.exam.examserver.models.Users;

public interface UserService {
	public Users createUser(Users user, Set<UserRole> userRoles) throws Exception;
	public Users getUser(String username);
	public void deleteUser(Long userId);

}
