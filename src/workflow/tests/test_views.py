# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import os

from django.conf import settings
from django.shortcuts import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

import test
from dataops import pandas_db
from workflow.models import Workflow


class WorkflowInitial(test.OntaskLiveTestCase):
    def setUp(self):
        super(WorkflowInitial, self).setUp()
        test.create_users()

    def test_00_home_view(self):
        for uemail, ucode in [('student1@bogus.com', 302),
                              ('instructor1@bogus.com', 200),
                              ('ainstructor1@bogus.com', 200),
                              ('idesigner1@bogus.com', 200),
                              ('aidesigner1@bogus.com', 200),
                              ('superuser@bogus.com', 200)]:
            user_login = self.client.login(email=uemail,
                                           password=test.boguspwd)
            self.assertTrue(user_login)

            response = self.client.get(reverse('workflow:index'))

            # Should redirect to a page with the profile (it is not staff).
            self.assertEqual(response.status_code, ucode)

            self.client.logout()

    def test_01_workflow_create_upload_merge_column_edit(self):
        """
        Create a workflow, upload data and merge
        :return:
        """

        # Login
        self.login('idesigner1@bogus.com')

        self.open(reverse('workflow:index'))

        # GO TO THE WORKFLOW PAGE
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Workflows'))
        self.assertIn('New Workflow', self.selenium.page_source)
        self.assertIn('Import', self.selenium.page_source)

        # Create the workflow if not present
        if test.wflow_desc not in self.selenium.page_source:
            self.selenium.find_element_by_class_name(
                'js-create-workflow').click()
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, 'id_name')))

            self.selenium.find_element_by_id('id_name').send_keys(
                test.wflow_name
            )
            desc = self.selenium.find_element_by_id('id_description_text')
            desc.send_keys(test.wflow_desc)
            desc.send_keys(Keys.RETURN)
            # Wait for workflows page
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable(
                    (By.LINK_TEXT, test.wflow_name)
                )
            )

        # Verify that the workflow is now part of the catalog
        self.assertIn(test.wflow_name, self.selenium.page_source)
        self.assertIn(test.wflow_desc, self.selenium.page_source)

        # Open the workflow
        wf_link = self.selenium.find_element_by_link_text(test.wflow_name)
        wf_link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'wflow-name')))

        if test.wflow_empty not in self.selenium.page_source:
            # The workflow has data. Proceed to flush
            flush = self.selenium.find_element_by_class_name(
                'js-workflow-flush'
            )
            flush.click()
            WebDriverWait(self.selenium, 10).until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'lead'), test.wflow_name))
            go_flush = self.selenium.find_element_by_xpath(
                "//button[@type='submit']"
            )
            # CONFIRM
            go_flush.click()
            # Wait for the flush to occur
            WebDriverWait(self.selenium, 10).until(
                EC.text_to_be_present_in_element(
                    (By.ID, 'wflow-empty'), test.wflow_empty))

        # Goto Dataops list
        self.open(reverse('dataops:list'))
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Dataops')
        )
        # Click in the upload/Merge link
        upload = self.selenium.find_element_by_xpath(
            "//tbody/tr/td/a[1]"
        )

        # Goto Upload/Merge CSV
        upload.click()
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Upload/Merge CSV')
        )

        # Set the file name
        self.selenium.find_element_by_id('id_file').send_keys(
            os.path.join(settings.PROJECT_PATH,
                         '..',
                         'test_data',
                         'simple.csv')
        )

        # Click on the NEXT button
        self.selenium.find_element_by_xpath(
            "//button[@name='Submit']"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'page-header'),
                                             'Step 2: Select Columns')
        )

        # Select all the columns
        self.selenium.find_element_by_id('checkAll').click()

        # Change the name of one of the columns
        input_email = self.selenium.find_element_by_xpath(
            "//table[@id='workflow-table']/tbody/tr[3]/td[5]/input"
        )
        input_email.clear()
        input_email.send_keys('email')

        # Click on the FINISH button
        self.selenium.find_element_by_xpath(
            "//button[@name='Submit']"
        ).click()
        # Wait for the upload/merge
        WebDriverWait(self.selenium, 20).until(
            EC.title_is('Ontask :: Dataops')
        )

        # Goto Details list
        self.selenium.find_element_by_link_text('Details').click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'page-header'),
                                             'Workflow Details')
        )

        # First column must be: age, double
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[1]/td[1]").text,
                         'age')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[1]/td[2]").text,
                         'double')

        # Second column must be email string
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[2]/td[1]").text,
                         'email')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[2]/td[2]").text,
                         'string')

        # Third column must be sid integer
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[3]/td[1]").text,
                         'sid')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[3]/td[2]").text,
                         'integer')

        # Fourth column must be name string
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[4]/td[1]").text,
                         'name')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[4]/td[2]").text,
                         'string')

        # Fifth registered and boolean
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[5]/td[1]").text,
                         'registered')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[5]/td[2]").text,
                         'boolean')

        # Sixth when and datetime
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[6]/td[1]").text,
                         'when')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[6]/td[2]").text,
                         'datetime')

        # Number of key columns
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//div[@id='workflow-table']/p[@class='help-block']/mark").text,
                         '3 Key columns')

        # Goto Dataops list
        self.open(reverse('dataops:list'))
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Dataops')
        )
        # Click in the upload/Merge link
        upload = self.selenium.find_element_by_xpath(
            "//tbody/tr/td/a[1]"
        )

        # Goto Upload/Merge CSV
        upload.click()
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Upload/Merge CSV')
        )

        # Set the file name
        self.selenium.find_element_by_id('id_file').send_keys(
            os.path.join(settings.PROJECT_PATH,
                         '..',
                         'test_data',
                         'simple2.csv')
        )

        # Click on the NEXT button
        self.selenium.find_element_by_xpath(
            "//button[@name='Submit']"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'page-header'),
                                             'Step 2: Select Columns')
        )

        # Select all the columns
        self.selenium.find_element_by_id('checkAll').click()

        # Change the name of sid2 to sid
        input_email = self.selenium.find_element_by_xpath(
            "//table[@id='workflow-table']/tbody/tr[3]/td[5]/input"
        )
        input_email.clear()
        input_email.send_keys('sid')

        # Click on the Next button
        self.selenium.find_element_by_xpath(
            "//button[@name='Submit']"
        ).click()
        # Wait for the upload/merge
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'page-header'),
                'Step 3: Select Unique Keys to Merge')
        )

        # Select SID in the first key
        self.selenium.find_element_by_id('id_dst_key').send_keys('sid')
        # Select SID in the first key
        self.selenium.find_element_by_id('id_src_key').send_keys('sid')

        # Click on the Next button
        self.selenium.find_element_by_xpath(
            "//button[@name='Submit']"
        ).click()
        # Wait for the upload/merge
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'page-header'),
                'Step 4: Review and confirm')
        )

        # Click on the FINISH button
        self.selenium.find_element_by_xpath(
            "//button[@name='Submit']"
        ).click()
        # Wait for the upload/merge
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Dataops')
        )

        # Goto Dataops list
        self.selenium.find_element_by_link_text('Details').click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'page-header'),
                                             'Workflow Details')
        )
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success'))
        )

        # Fourth column must be: another, string
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[4]/td[1]").text,
                         'another')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[4]/td[2]").text,
                         'string')

        # Sixth column must be one string
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[6]/td[1]").text,
                         'one')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[6]/td[2]").text,
                         'string')

        # Number of key columns
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//div[@id='workflow-table']/p[@class='help-block']/mark").text,
                         '3 Key columns')
        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)


class WorkflowModify(test.OntaskLiveTestCase):
    fixtures = ['simple_workflow']
    filename = os.path.join(
        settings.PROJECT_PATH,
        'workflow',
        'fixtures',
        'simple_workflow_df.sql'
    )

    def setUp(self):
        super(WorkflowModify, self).setUp()
        pandas_db.pg_restore_table(self.filename)

    def tearDown(self):
        pandas_db.delete_all_tables()
        super(WorkflowModify, self).tearDown()

    def test_02_workflow_column_create_delete(self):
        new_cols = [
            ('newc1', 'string', 'male,female', ''),
            ('newc2', 'boolean', '', 'True'),
            ('newc3', 'integer', '0, 10, 20, 30', '0'),
            ('newc4', 'double', '0, 0.5, 1, 1.5, 2', '0'),
            ('newc5', 'datetime', '', '2017-10-11 00:00:00.000+11:00'),
        ]

        # Login
        self.login('idesigner1@bogus.com')

        self.open(reverse('workflow:index'))

        # GO TO THE WORKFLOW PAGE
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Workflows'))
        self.assertIn('New Workflow', self.selenium.page_source)
        self.assertIn('Import', self.selenium.page_source)

        # Open the workflow
        wf_link = self.selenium.find_element_by_link_text(test.wflow_name)
        wf_link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success'))
        )

        # Edit the age column
        self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[1]/td[4]/button[1]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'modal-title'),
                                             'Edit column')
        )
        # Untick the is_key option
        is_key = self.selenium.find_element_by_id('id_is_key')
        self.assertTrue(is_key.is_selected())
        is_key.click()
        # Click on the Submit button
        self.selenium.find_element_by_xpath(
            "//div[@id='modal-item']/div/div/form/div/button[@type='submit']"
        ).click()
        with self.wait_for_page_load(timeout=10):
            self.selenium.find_element_by_link_text('Details')
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success'))
        )

        # Third column must be age, double
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[3]/td[1]").text,
                         'age')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[3]/td[2]").text,
                         'double')

        # ADD COLUMNS
        for cname, ctype, clist, cinit in new_cols:
            # ADD A NEW COLUMN
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, 'js-workflow-column-add'))
            )
            self.selenium.find_element_by_class_name(
                'js-workflow-column-add').click()
            WebDriverWait(self.selenium, 10).until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'modal-title'),
                    'Add column'
                )
            )
            # Set the fields
            self.selenium.find_element_by_id('id_name').send_keys(cname)
            select = Select(self.selenium.find_element_by_id(
                'id_data_type'))
            select.select_by_value(ctype)
            if clist:
                self.selenium.find_element_by_id(
                    'id_raw_categories').send_keys(clist)
            if cinit:
                self.selenium.find_element_by_id(
                    'id_initial_value'
                ).send_keys(cinit)
            # Click on the Submit button
            self.selenium.find_element_by_xpath(
                "//div[@id='modal-item']/div/div/form/div[@class='modal-footer']/button[@type='submit']"
            ).click()
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'success'))
            )
            pandas_db.check_wf_df(Workflow.objects.get(pk=1))

        # CHECK THAT THE COLUMNS HAVE BEEN CREATED (starting in the sixth)
        idx = 6
        for cname, ctype, _, _ in new_cols:
            row_path1 = "//table[@id='column-table']/tbody/tr[{0}]/td[1]"
            row_path2 = "//table[@id='column-table']/tbody/tr[{0}]/td[2]"

            # Third column must be age, double
            self.assertEqual(self.selenium.find_element_by_xpath(
                row_path1.format(idx)).text,
                             cname)
            self.assertEqual(self.selenium.find_element_by_xpath(
                row_path2.format(idx)).text,
                             ctype)
            idx += 1

        # DELETE THE COLUMNS
        for cname, ctype, _, _ in new_cols:
            row_prefix = "//table[@id='column-table']/tbody/tr[6]/td[4]"
            self.selenium.find_element_by_xpath(
                row_prefix + "/button[2]"
            ).click()
            WebDriverWait(self.selenium, 10).until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'modal-title'),
                    'Confirm column deletion')
            )
            self.selenium.find_element_by_xpath(
                "//div[@id='modal-item']//button[@type='submit']"
            ).click()
            # Wait for the details page
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'success'))
            )

        # Sixth column must be one string
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[6]/td[1]").text,
                         'one')
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[6]/td[2]").text,
                         'string')

        # End of session
        self.logout()

    def test_03_workflow_column_rename(self):
        categories = 'aaa, bbb, ccc'
        action_name = 'simple action'
        action_desc = 'action description text'

        # Login
        self.login('idesigner1@bogus.com')

        self.open(reverse('workflow:index'))

        # GO TO THE WORKFLOW PAGE
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Workflows'))
        self.assertIn('New Workflow', self.selenium.page_source)
        self.assertIn('Import', self.selenium.page_source)

        # Open the workflow
        wf_link = self.selenium.find_element_by_link_text(test.wflow_name)
        wf_link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'wflow-name')))
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success'))
        )

        # Edit the another column
        self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[4]/td[4]/button[1]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'modal-title'),
                                             'Edit column')
        )
        # Change the name of the column
        self.selenium.find_element_by_id('id_name').send_keys('2')
        # Add list of comma separated categories
        raw_cat = self.selenium.find_element_by_id(
            'id_raw_categories'
        )
        raw_cat.send_keys(categories)
        # Click in the rename button
        self.selenium.find_element_by_xpath(
            "//div[@id='modal-item']/div/div/form/div/button[@type='submit']"
        ).click()
        # MODAL WAITING
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success'))
        )

        # Fourth column must now have name another2
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[4]/td[1]").text,
                         'another2')

        # Goto the action page
        self.selenium.find_element_by_link_text('Actions').click()
        # Wait for page to refresh (FLAKY)
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, 'js-create-action')
            )
        )
        self.assertIn('New Action', self.selenium.page_source)

        # click in the create action button
        self.selenium.find_element_by_class_name(
            'js-create-action').click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'id_name')))

        # Set the name and description of the action
        self.selenium.find_element_by_id('id_name').send_keys(action_name)
        desc = self.selenium.find_element_by_id('id_description_text')
        desc.send_keys(action_desc)
        desc.send_keys(Keys.RETURN)
        # Wait for workflows page
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@id='filter-set']/h4/button")
            )
        )

        # Click in the add filter button
        self.selenium.find_element_by_xpath(
            "//div[@id='filter-set']/h4/button"
        ).click()
        # Select the another2 column (with new name
        select = Select(self.selenium.find_element_by_name(
            'builder_rule_0_filter'))
        select.select_by_value('another2')
        # Wait for the select elements to be clickable
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//select[@name='builder_rule_0_filter']")
            )
        )

        # There should only be two operands
        filter_ops = self.selenium.find_elements_by_xpath(
            "//select[@name='builder_rule_0_operator']/option"
        )
        self.assertEqual(len(filter_ops), 2)

        # There should be as many values as in the categories
        filter_vals = self.selenium.find_elements_by_xpath(
            "//select[@name='builder_rule_0_value_0']/option"
        )
        self.assertEqual(len(filter_vals), len(categories.split(',')))

        # End of session
        self.logout()


class WorkflowAttribute(test.OntaskLiveTestCase):
    fixtures = ['simple_workflow']
    filename = os.path.join(
        settings.PROJECT_PATH,
        'workflow',
        'fixtures',
        'simple_workflow_df.sql'
    )

    def setUp(self):
        super(WorkflowAttribute, self).setUp()
        pandas_db.pg_restore_table(self.filename)

    def tearDown(self):
        pandas_db.delete_all_tables()
        super(WorkflowAttribute, self).tearDown()

    def test_workflow_attributes(self):
        categories = 'aaa, bbb, ccc'
        action_name = 'simple action'
        action_desc = 'action description text'

        # Login
        self.login('idesigner1@bogus.com')

        self.open(reverse('workflow:index'))

        # GO TO THE WORKFLOW PAGE
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('Ontask :: Workflows'))
        self.assertIn('New Workflow', self.selenium.page_source)
        self.assertIn('Import', self.selenium.page_source)

        # Open the workflow
        wf_link = self.selenium.find_element_by_link_text(test.wflow_name)
        wf_link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'wflow-name')))

        # Click on the attributes
        self.selenium.find_element_by_link_text('Attributes').click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'js-attribute-create')))

        # Attributes are initially empty
        self.assertIn('No attributes defined', self.selenium.page_source)

        # Click in the create attribute dialog
        self.selenium.find_element_by_class_name('js-attribute-create').click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'modal-title'),
                'Create a new attribute'))

        # Fill out the form
        self.selenium.find_element_by_id('id_key').send_keys('key1')
        self.selenium.find_element_by_id('id_value').send_keys('value1')

        # Click in the create atribute button
        self.selenium.find_element_by_xpath(
            "//div[@class='modal-footer']/button[2]"
        ).click()
        # MODAL WAITING
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # Values now should be in the table
        self.assertEqual(
            self.selenium.find_element_by_id('id_key1').get_attribute('value'),
            'key1'
        )
        self.assertEqual(
            self.selenium.find_element_by_id(
                'id_key1__value').get_attribute('value'),
            'value1'
        )

        # Click in the create attribute dialog again
        self.selenium.find_element_by_class_name('js-attribute-create').click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'modal-title'),
                'Create a new attribute'))

        # Fill out the form
        self.selenium.find_element_by_id('id_key').send_keys('key2')
        self.selenium.find_element_by_id('id_value').send_keys('value2')

        # Click in the create atribute button
        self.selenium.find_element_by_xpath(
            "//div[@class='modal-footer']/button[2]"
        ).click()
        # MODAL WAITING
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # Values now should be in the table
        key2 = self.selenium.find_element_by_id('id_key2')
        value2 = self.selenium.find_element_by_id('id_key2__value')
        self.assertEqual(key2.get_attribute('value'), 'key2')
        self.assertEqual(value2.get_attribute('value'), 'value2')

        # Rename second attribute
        key2.clear()
        key2.send_keys('newkey2')
        value2.clear()
        value2.send_keys('newvalue2')

        # Click in the save and close
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-attributes']/form/button[@type='submit']"
        ).click()
        # Wait for the details page
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'page-header'),
                                             'Workflow Details')
        )

        # Check that the attributes are properly stored in the workflow
        workflow = Workflow.objects.all()[0]
        self.assertEqual(len(workflow.attributes), 2)
        self.assertEqual(workflow.attributes['key1'], 'value1')
        self.assertEqual(workflow.attributes['newkey2'], 'newvalue2')

        # Go back to the attribute page
        self.selenium.find_element_by_link_text('Attributes').click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'js-attribute-create')))

        # click the delete button in the second row
        self.selenium.find_element_by_xpath(
            "//table[@id='attribute-table']/tbody/tr[2]/td[1]/button[1]"
        ).click()
        # Wait for the delete confirmation frame
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'modal-title'),
                                             'Confirm attribute deletion')
        )
        # Click in the delete confirm button
        self.selenium.find_element_by_xpath(
            "//div[@class='modal-footer']/button[2]"
        ).click()
        # MODAL WAITING
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # There should only be a single element
        self.assertEqual(
            len(self.selenium.find_elements_by_xpath(
                "//table[@id='attribute-table']/tbody/tr"
            )),
            1
        )
        # Check that the attributes are properly stored in the workflow
        workflow = Workflow.objects.all()[0]
        self.assertEqual(len(workflow.attributes), 1)
        self.assertEqual(workflow.attributes['key1'], 'value1')

        # End of session
        self.logout()