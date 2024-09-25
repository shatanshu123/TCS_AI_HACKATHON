package com.exam.examserver;

import java.util.HashSet;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import com.exam.examserver.models.Role;
import com.exam.examserver.models.UserRole;
import com.exam.examserver.models.Users;
import com.exam.examserver.services.UserService;

@SpringBootApplication
public class ExamserverApplication implements CommandLineRunner{
	@Autowired
	private UserService userService;

	public static void main(String[] args) {
		SpringApplication.run(ExamserverApplication.class, args);
	}

	@Override
	public void run(String... args) throws Exception {
		// TODO Auto-generated method stub
		System.out.println("starting code....");
		/*
		 * Users user=new Users(); user.setFirstName("Shatanshu");
		 * user.setLastName("Agarwal"); user.setUsername("shatanshu_007");
		 * user.setPassword("qwerty123"); user.setEmail("abc@gnail.com");
		 * user.setProfile("default.png");
		 * 
		 * Role role1=new Role(); role1.setRoleId(44L); role1.setRoleName("ADMIN");
		 * 
		 * Set<UserRole> userRoleSet = new HashSet<>(); UserRole userRole=new
		 * UserRole(); userRole.setRole(role1); userRole.setUser(user);
		 * userRoleSet.add(userRole); Users users=this.userService.createUser(user,
		 * userRoleSet); System.out.println(users.getUsername());
		 */
		
	}
	
}