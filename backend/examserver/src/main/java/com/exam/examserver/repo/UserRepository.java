package com.exam.examserver.repo;

import org.springframework.data.jpa.repository.JpaRepository;

import com.exam.examserver.models.Users;

public interface UserRepository extends JpaRepository<Users,Long>{
	
	public Users findByUsername(String Username);
}
